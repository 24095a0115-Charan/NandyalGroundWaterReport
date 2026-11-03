// Global state for Plotly charts and data
let globalData = null;
let currentSelectedModel = 'Ensemble';
let showRainfallOverlay = true;

document.addEventListener('DOMContentLoaded', async () => {
  initDayNightMode();
  await fetchDashboardData();
  await fetchBenchmarkData();
  
  window.addEventListener('resize', () => {
    if (document.getElementById('groundwaterPlotly')) Plotly.Plots.resize('groundwaterPlotly');
    if (document.getElementById('quantityPlotly')) Plotly.Plots.resize('quantityPlotly');
  });
});

/* Safe Helper to set textContent without throwing TypeError on missing DOM elements */
function safeSetText(id, text) {
  const el = document.getElementById(id);
  if (el) {
    el.textContent = text !== undefined && text !== null ? text : '--';
  }
}

/* Day & Night Mode Handler */
function initDayNightMode() {
  const savedTheme = localStorage.getItem('hydro_theme') || 'dark';
  if (savedTheme === 'light') {
    document.body.classList.add('light-mode');
    updateDNButtonUI(true);
  } else {
    document.body.classList.remove('light-mode');
    updateDNButtonUI(false);
  }
}

function toggleDayNightMode() {
  const isLight = document.body.classList.toggle('light-mode');
  localStorage.setItem('hydro_theme', isLight ? 'light' : 'dark');
  updateDNButtonUI(isLight);
  
  if (globalData) {
    renderGroundwaterPlotly(currentSelectedModel);
    renderQuantityPlotly();
    updateScenario();
  }
}

function updateDNButtonUI(isLight) {
  const icon = document.getElementById('dnIcon');
  const label = document.getElementById('dnLabel');
  if (icon && label) {
    icon.textContent = isLight ? '☀️' : '🌙';
    label.textContent = isLight ? 'Day Mode' : 'Night Mode';
  }
}

async function fetchDashboardData() {
  try {
    const res = await fetch('/api/data');
    globalData = await res.json();
    
    populateMetricCards(globalData.summary, globalData.historical ? globalData.historical[globalData.historical.length - 1] : null);
  } catch (err) {
    console.error('Error fetching metric summary:', err);
  }
  
  try {
    renderGroundwaterPlotly(currentSelectedModel);
  } catch (err) {
    console.error('Error rendering groundwater chart:', err);
  }
  
  try {
    renderQuantityPlotly();
  } catch (err) {
    console.error('Error rendering quantity storage chart:', err);
  }
}

async function fetchBenchmarkData() {
  try {
    const res = await fetch('/api/benchmark');
    const metrics = await res.json();
    
    const tbody = document.getElementById('benchmarkTbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    for (const [model, stats] of Object.entries(metrics)) {
      const tr = document.createElement('tr');
      if (model === 'Ensemble') {
        tr.classList.add('highlight-row');
      }
      
      const isR2Good = stats.R2 >= 0.40;
      
      tr.innerHTML = `
        <td><strong>${model} ${model === 'Ensemble' ? '⭐ (Optimal)' : ''}</strong></td>
        <td>${stats.RMSE.toFixed(3)}</td>
        <td>${stats.MAE.toFixed(3)}</td>
        <td class="${isR2Good ? 'metric-pass' : ''}">${stats.R2.toFixed(3)}</td>
        <td>${stats.MAPE}%</td>
      `;
      tbody.appendChild(tr);
    }
  } catch (err) {
    console.error('Error fetching benchmark metrics:', err);
  }
}

function populateMetricCards(summary, latestRecord) {
  if (!summary) return;
  
  safeSetText('val-water-level', summary.latest_water_level_mbgl);
  safeSetText('val-last-date', summary.latest_reading_date);
  safeSetText('val-storage-mcm', summary.latest_quantity_mcm);
  
  if (summary.latest_wqi) {
    safeSetText('val-wqi-score', summary.latest_wqi);
    safeSetText('val-wqi-status', summary.latest_wqi_status);
  }
  
  // Rainfall & Recharge Link Metrics
  if (summary.rainfall_gw_link) {
    const link = summary.rainfall_gw_link;
    const corrSign = link.seasonal_recharge_correlation >= 0 ? '+' : '';
    safeSetText('val-rain-corr', `${corrSign}${link.seasonal_recharge_correlation}`);
    safeSetText('val-annual-rain', link.annual_average_rainfall_mm);
    safeSetText('val-latest-rain', `${summary.latest_rainfall_mm || 0} mm`);
    safeSetText('val-recharge-rate', `~${link.recharge_mcm_per_100mm} MCM / 100mm`);
    
    safeSetText('stat-seasonal-corr', `${corrSign}${link.seasonal_recharge_correlation}`);
    safeSetText('stat-depth-corr', `${link.depth_inverse_correlation} (Shallower depth = Higher water table)`);
    safeSetText('stat-mcm-per-100mm', `~${link.recharge_mcm_per_100mm} MCM`);
    safeSetText('stat-rise-per-100mm', `~${link.water_table_rise_m_per_100mm} meters rise`);
    safeSetText('stat-monsoon-rain', `~${link.monsoon_monthly_avg_mm} mm / mo`);
    safeSetText('stat-dry-rain', `~${link.non_monsoon_monthly_avg_mm} mm / mo`);
  }
  
  if (latestRecord && latestRecord.water_quality) {
    const wq = latestRecord.water_quality;
    safeSetText('wq-ph', wq.pH);
    safeSetText('wq-ec', `${wq.EC} µS/cm`);
    safeSetText('wq-tds', `${wq.TDS} mg/L`);
    safeSetText('wq-nitrate', `${wq.Nitrate} mg/L`);
    safeSetText('wq-fluoride', `${wq.Fluoride} mg/L`);
  }
}

function getPlotlyTheme() {
  const isLight = document.body.classList.contains('light-mode');
  return {
    bgColor: 'rgba(0, 0, 0, 0.0)',
    fontColor: isLight ? '#334155' : '#94a3b8',
    gridColor: isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.06)'
  };
}

function toggleRainfallOverlay() {
  showRainfallOverlay = !showRainfallOverlay;
  const btn = document.getElementById('btnToggleRain');
  if (btn) {
    btn.classList.toggle('active', showRainfallOverlay);
  }
  renderGroundwaterPlotly(currentSelectedModel);
  updateScenario();
}

function renderGroundwaterPlotly(modelName = 'Ensemble') {
  if (!globalData || !document.getElementById('groundwaterPlotly')) return;
  
  const theme = getPlotlyTheme();
  const histDates = globalData.historical.map(h => h.month);
  const histValues = globalData.historical.map(h => h.water_level_mbgl);
  const histRainfall = globalData.historical.map(h => h.rainfall_mm !== undefined ? h.rainfall_mm : 0);
  
  const fcDates = globalData.forecast.map(f => f.month);
  const fcValues = globalData.forecast.map(f => f[modelName] !== undefined ? f[modelName] : f.Ensemble);
  const fcRainfall = globalData.forecast.map(f => f.rainfall_mm !== undefined ? f.rainfall_mm : 0);
  const upperBounds = globalData.forecast.map(f => f.Upper_Bound || (f[modelName] + 0.8));
  const lowerBounds = globalData.forecast.map(f => f.Lower_Bound || Math.max(1.0, f[modelName] - 0.8));
  
  const traces = [];

  // 1. Rainfall Hyetograph Bar Trace (Dual-Axis yaxis2)
  if (showRainfallOverlay) {
    const traceRainfall = {
      x: [...histDates, ...fcDates],
      y: [...histRainfall, ...fcRainfall],
      type: 'bar',
      name: 'Rainfall / Precipitation (mm)',
      yaxis: 'y2',
      marker: {
        color: 'rgba(56, 189, 248, 0.28)',
        line: { color: 'rgba(56, 189, 248, 0.75)', width: 1 }
      },
      hovertemplate: '%{x}<br>Rainfall: <b>%{y} mm</b><extra></extra>'
    };
    traces.push(traceRainfall);
  }

  // 2. Historical Groundwater Level Line
  const traceHist = {
    x: histDates,
    y: histValues,
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Historical Groundwater (m bgl)',
    line: { color: '#06b6d4', width: 3 },
    marker: { size: 5 },
    hovertemplate: '%{x}<br>Depth: <b>%{y} m bgl</b><extra></extra>'
  };
  traces.push(traceHist);

  // 3. 95% Confidence Band
  const traceUpper = {
    x: fcDates,
    y: upperBounds,
    type: 'scatter',
    mode: 'lines',
    line: { width: 0 },
    showlegend: false,
    hoverinfo: 'skip'
  };
  const traceLower = {
    x: fcDates,
    y: lowerBounds,
    type: 'scatter',
    mode: 'lines',
    fill: 'tonexty',
    fillcolor: 'rgba(139, 92, 246, 0.15)',
    line: { width: 0 },
    name: '95% Confidence Band',
    hoverinfo: 'skip'
  };
  traces.push(traceUpper, traceLower);

  // 4. ML Forecast Line
  const traceFc = {
    x: [histDates[histDates.length - 1], ...fcDates],
    y: [histValues[histValues.length - 1], ...fcValues],
    type: 'scatter',
    mode: 'lines+markers',
    name: `ML Forecast (${modelName})`,
    line: { color: '#8b5cf6', width: 3, dash: 'dash' },
    marker: { size: 5, color: '#8b5cf6' },
    hovertemplate: '%{x}<br>Forecast: <b>%{y} m bgl</b><extra></extra>'
  };
  traces.push(traceFc);

  const layout = {
    paper_bgcolor: theme.bgColor,
    plot_bgcolor: theme.bgColor,
    font: { family: 'Outfit, Inter, sans-serif', color: theme.fontColor },
    margin: { l: 55, r: 55, t: 25, b: 40 },
    legend: { orientation: 'h', y: 1.15, x: 0 },
    xaxis: { gridcolor: theme.gridColor, zerolinecolor: theme.gridColor, nticks: 12 },
    yaxis: { 
      autorange: 'reversed', 
      title: 'Water Level Depth (m bgl) [Inverted: Higher = Shallower/Fuller]', 
      gridcolor: theme.gridColor, 
      zerolinecolor: theme.gridColor 
    },
    yaxis2: {
      title: 'Monthly Rainfall (mm)',
      overlaying: 'y',
      side: 'right',
      range: [0, 240],
      showgrid: false,
      zeroline: false
    },
    hovermode: 'x unified',
    bargap: 0.25
  };

  const config = { responsive: true, displayModeBar: true, displaylogo: false };
  Plotly.react('groundwaterPlotly', traces, layout, config);
}

/* Dynamic Aquifer Storage Volume (MCM) Chart - Complete 2022-2030 Timeline */
function renderQuantityPlotly() {
  if (!globalData || !document.getElementById('quantityPlotly')) return;
  
  const theme = getPlotlyTheme();
  
  const histDates = globalData.historical.map(h => h.month);
  const histQuantities = globalData.historical.map(h => h.quantity_mcm);
  
  const fcDates = globalData.forecast.map(f => f.month);
  const fcQuantities = globalData.forecast.map(f => f.quantity_mcm);
  
  const traceHistQty = {
    x: histDates,
    y: histQuantities,
    type: 'bar',
    name: 'Historical Storage (MCM)',
    marker: {
      color: '#06b6d4',
      opacity: 0.85,
      line: { color: '#0284c7', width: 1 }
    },
    hovertemplate: '%{x}<br>Historical Storage: <b>%{y} MCM</b><extra></extra>'
  };

  const traceFcQty = {
    x: fcDates,
    y: fcQuantities,
    type: 'bar',
    name: 'Forecasted Storage (MCM)',
    marker: {
      color: '#8b5cf6',
      opacity: 0.85,
      line: { color: '#7c3aed', width: 1 }
    },
    hovertemplate: '%{x}<br>Forecast Storage: <b>%{y} MCM</b><extra></extra>'
  };

  const layout = {
    paper_bgcolor: theme.bgColor,
    plot_bgcolor: theme.bgColor,
    font: { family: 'Outfit, Inter, sans-serif', color: theme.fontColor },
    margin: { l: 55, r: 20, t: 20, b: 40 },
    legend: { orientation: 'h', y: 1.15, x: 0 },
    xaxis: { gridcolor: theme.gridColor, showgrid: false, nticks: 12 },
    yaxis: { title: 'Usable Aquifer Storage (MCM)', gridcolor: theme.gridColor, zerolinecolor: theme.gridColor },
    hovermode: 'x unified'
  };

  const config = { responsive: true, displayModeBar: true, displaylogo: false };
  Plotly.react('quantityPlotly', [traceHistQty, traceFcQty], layout, config);
}

function selectModelChart(modelName) {
  currentSelectedModel = modelName;
  document.querySelectorAll('.btn-toggle').forEach(btn => {
    if (btn.getAttribute('data-model')) {
      btn.classList.toggle('active', btn.getAttribute('data-model') === modelName);
    }
  });
  renderGroundwaterPlotly(modelName);
  updateScenario();
}

async function updateScenario() {
  const rainfallEl = document.getElementById('slider-rainfall');
  const extractionEl = document.getElementById('slider-extraction');
  const horizonEl = document.getElementById('slider-horizon');
  
  if (!rainfallEl || !extractionEl || !horizonEl) return;

  const rainfall = parseFloat(rainfallEl.value);
  const extraction = parseFloat(extractionEl.value);
  const horizon = parseInt(horizonEl.value);
  
  safeSetText('lbl-rainfall', `${rainfall > 0 ? '+' : ''}${rainfall}%`);
  safeSetText('lbl-extraction', `${extraction}x`);
  safeSetText('lbl-horizon', `${horizon} M`);
  
  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rainfall_anomaly_pct: rainfall,
        extraction_factor: extraction,
        horizon_months: horizon,
        selected_model: currentSelectedModel
      })
    });
    
    const result = await res.json();
    if (result.status === 'success') {
      const simData = result.simulated_forecast;
      const lastSim = simData[simData.length - 1];
      const baseFinal = simData[simData.length - 1].baseline_water_level_mbgl;
      const simDeltaM = (baseFinal - lastSim.simulated_water_level_mbgl).toFixed(2);
      
      const summaryEl = document.getElementById('sim-impact-summary');
      if (summaryEl) {
        const rechargeMsg = rainfall > 0
          ? `<span style="color: var(--accent-emerald); font-weight:700;">+${rainfall}% Extra Rain recharges aquifer (+${Math.abs(simDeltaM)}m higher water table)</span>`
          : rainfall < 0
          ? `<span style="color: var(--accent-rose); font-weight:700;">${rainfall}% Rainfall Deficit depletes aquifer (${Math.abs(simDeltaM)}m deeper water table)</span>`
          : `<span>Normal rainfall conditions</span>`;
          
        summaryEl.innerHTML = `
          Projected at <strong>${lastSim.month}</strong>: 
          <span style="color: ${lastSim.color}; font-weight:700;">${lastSim.simulated_water_level_mbgl} m bgl</span> 
          (Usable Storage: <strong>${lastSim.quantity_mcm} MCM</strong>, Status: <span class="${lastSim.status === 'Safe' ? 'badge-safe' : 'badge-critical'}">${lastSim.status}</span>).<br>
          <strong>Hydro Dynamic Impact:</strong> ${rechargeMsg}.
        `;
      }
      
      if (globalData) {
        const histDates = globalData.historical.map(h => h.month);
        const histValues = globalData.historical.map(h => h.water_level_mbgl);
        
        const simTrace = {
          x: [histDates[histDates.length - 1], ...simData.map(s => s.month)],
          y: [histValues[histValues.length - 1], ...simData.map(s => s.simulated_water_level_mbgl)],
          type: 'scatter',
          mode: 'lines+markers',
          name: `Simulated Scenario (${rainfall > 0 ? '+' : ''}${rainfall}% Rain, ${extraction}x Extract)`,
          line: { color: '#f43f5e', width: 2.5, dash: 'dot' },
          marker: { size: 5, color: '#f43f5e' },
          hovertemplate: '%{x}<br>Simulated Level: <b>%{y} m bgl</b><extra></extra>'
        };
        
        const graphDiv = document.getElementById('groundwaterPlotly');
        if (graphDiv && graphDiv.data) {
          const currentTraces = graphDiv.data.filter(t => !t.name || !t.name.includes('Simulated Scenario'));
          currentTraces.push(simTrace);
          Plotly.react('groundwaterPlotly', currentTraces, graphDiv.layout);
        }

        const simQtyTrace = {
          x: simData.map(s => s.month),
          y: simData.map(s => s.quantity_mcm),
          type: 'bar',
          name: `Simulated Storage (${rainfall > 0 ? '+' : ''}${rainfall}% Rain)`,
          marker: {
            color: '#f43f5e',
            opacity: 0.75
          },
          hovertemplate: '%{x}<br>Simulated Storage: <b>%{y} MCM</b><extra></extra>'
        };

        const qtyDiv = document.getElementById('quantityPlotly');
        if (qtyDiv && qtyDiv.data) {
          const currentQtyTraces = qtyDiv.data.filter(t => !t.name || !t.name.includes('Simulated Storage'));
          currentQtyTraces.push(simQtyTrace);
          Plotly.react('quantityPlotly', currentQtyTraces, qtyDiv.layout);
        }
      }
    }
  } catch (err) {
    console.error('Error updating scenario simulation:', err);
  }
}
