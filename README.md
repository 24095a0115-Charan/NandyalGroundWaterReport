# Nandyal GroundWater Level & Rainwater Recharge ML Forecasting System

Final Year Engineering Project — Machine Learning Approach for GroundWater Level Forecasting, Rainwater Recharge Link Dynamics, and Quantity Prediction in Nandyal District, AP (2022–2030).

---

## 🌧️ Rainwater Recharge & GroundWater Link
The system integrates real-world rainfall measurements from `NANDYAL Rainwater data.xlsx` (2022–2026) alongside groundwater levels:
- **Positive Seasonal Correlation**: $+0.63$ Pearson correlation between seasonal precipitation and usable groundwater storage.
- **Inverted Depth Correlation**: $-0.63$ between rainfall and water depth mbgl (higher rainfall $\implies$ shallower depth $\implies$ rising water table).
- **Aquifer Infiltration Yield**: Based on Central Ground Water Board (CGWB) norms for Nandyal's fractured rock aquifer ($S_y = 2.5\%$, Area = $9,682\text{ km}^2$), every $100\text{ mm}$ of rainfall contributes $\approx 116.2\text{ MCM}$ of fresh aquifer recharge, elevating the regional water table by $\approx 0.48\text{ meters}$.
- **Dual-Axis Hydrograph-Hyetograph**: Live Plotly interactive visualization overlaying the monthly rainfall hyetograph (bars, mm) directly with historical and forecasted groundwater levels (mbgl).

---

## 🚀 Live Render Deployment Instructions

### Automatic Deployment via Render Web Service
1. Log in to [Render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository: `https://github.com/24095a0115-Charan/NandyalGroundWaterReport.git`.
4. Configure the Web Service settings:
   - **Name**: `nandyal-groundwater-ml`
   - **Environment**: `Python 3`
   - **Region**: Any (e.g. Oregon / Singapore)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt && python run_pipeline.py`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
5. Click **Create Web Service**.

---

## 🛠️ Local Instructions for VS Code

### Step 1: Open Project Folder in VS Code
1. Open **VS Code**.
2. Click **File** -> **Open Folder...** -> Select `C:\Users\pafro\OneDrive\Desktop\GrondWaterLavel`.

### Step 2: Install Dependencies & Run
```bash

pip install -r requirements.txt
python run_pipeline.py
python app.py
```

Open your browser at `http://127.0.0.1:5000`.
