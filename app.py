import os
import json
import io
import pandas as pd
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, jsonify, request, send_file

from src.quantity_calculator import calculate_groundwater_quantity, calculate_storage_delta, get_cgwb_status_zone
from src.water_quality import estimate_nandyal_water_quality, calculate_wqi
from run_pipeline import run_groundwater_ml_pipeline

app = Flask(__name__)

DATA_FILE = 'data/processed_results.json'

def get_processed_data():
    if not os.path.exists(DATA_FILE):
        return run_groundwater_ml_pipeline()
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/summary', methods=['GET'])
def api_summary():
    data = get_processed_data()
    return jsonify(data['summary'])

@app.route('/api/benchmark', methods=['GET'])
def api_benchmark():
    data = get_processed_data()
    return jsonify(data['benchmark_metrics'])

@app.route('/api/data', methods=['GET'])
def api_data():
    data = get_processed_data()
    return jsonify({
        'summary': data['summary'],
        'historical': data['historical'],
        'forecast': data['forecast']
    })

@app.route('/api/rainfall-link', methods=['GET'])
def api_rainfall_link():
    data = get_processed_data()
    return jsonify(data['summary'].get('rainfall_gw_link', {}))

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    req = request.get_json() or {}
    rainfall_anomaly_pct = float(req.get('rainfall_anomaly_pct', 0.0))  # -50% to +50%
    extraction_factor = float(req.get('extraction_factor', 1.0))        # 0.5x to 2.0x
    horizon_months = int(req.get('horizon_months', 52))                 # up to 52 months (2030)
    selected_model = req.get('selected_model', 'Ensemble')
    
    data = get_processed_data()
    base_forecasts = data['forecast'][:horizon_months]
    
    simulated_forecasts = []
    prev_level = data['historical'][-1]['water_level_mbgl']
    
    # Direct physical recharge response:
    # +10% rainfall anomaly injects extra recharge (water table rises, mbgl decreases)
    # Higher extraction draws down water table
    monthly_recharge_effect = (rainfall_anomaly_pct / 100.0) * 0.16
    monthly_extraction_effect = (extraction_factor - 1.0) * 0.20
    
    accumulated_shift = 0.0
    
    for idx, item in enumerate(base_forecasts):
        base_val = item.get(selected_model, item['Ensemble'])
        base_rain = item.get('rainfall_mm', 0.0)
        sim_rain = max(0.0, round(base_rain * (1.0 + rainfall_anomaly_pct / 100.0), 2))
        
        accumulated_shift += (monthly_extraction_effect - monthly_recharge_effect)
        sim_val = max(1.0, base_val + accumulated_shift)
        
        vol_mcm = float(calculate_groundwater_quantity(sim_val))
        status_info = get_cgwb_status_zone(sim_val)
        delta_mcm = float(calculate_storage_delta(sim_val, prev_level))
        prev_level = sim_val
        
        wq_params = estimate_nandyal_water_quality(sim_val, rainfall_anomaly_pct)
        wqi_info = calculate_wqi(wq_params)
        
        simulated_forecasts.append({
            'date': item['date'],
            'month': item['month'],
            'simulated_water_level_mbgl': round(sim_val, 3),
            'baseline_water_level_mbgl': round(base_val, 3),
            'simulated_rainfall_mm': sim_rain,
            'baseline_rainfall_mm': base_rain,
            'quantity_mcm': vol_mcm,
            'storage_delta_mcm': delta_mcm,
            'status': status_info['status'],
            'category': status_info['category'],
            'color': status_info['color'],
            'water_quality': wq_params,
            'wqi': wqi_info['wqi'],
            'wqi_status': wqi_info['status']
        })
        
    return jsonify({
        'status': 'success',
        'scenario': {
            'rainfall_anomaly_pct': rainfall_anomaly_pct,
            'extraction_factor': extraction_factor,
            'horizon_months': horizon_months,
            'selected_model': selected_model
        },
        'simulated_forecast': simulated_forecasts
    })

@app.route('/api/export', methods=['GET'])
def api_export():
    data = get_processed_data()
    
    hist_df = pd.DataFrame(data['historical'])
    hist_df['type'] = 'Historical'
    
    fc_df = pd.DataFrame(data['forecast'])
    fc_df['type'] = 'Forecast'
    fc_df['water_level_mbgl'] = fc_df['Ensemble']
    
    combined_df = pd.concat([
        hist_df,
        fc_df
    ], ignore_index=True)
    
    # Flatten nested water_quality dictionary if present
    if 'water_quality' in combined_df.columns:
        wq_df = pd.json_normalize(combined_df['water_quality']).add_prefix('wq_')
        combined_df = pd.concat([combined_df.drop(columns=['water_quality']), wq_df], axis=1)
        
    output = io.BytesIO()
    combined_df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='text/csv',
        download_name='Nandyal_GroundWater_Rainwater_2022_2030_ML_Forecast.csv',
        as_attachment=True
    )

if __name__ == '__main__':
    print("Starting Flask Nandyal HydroML Server (2022-2030)...")
    app.run(host='0.0.0.0', port=5000, debug=True)
