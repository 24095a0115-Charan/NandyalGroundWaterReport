# Nandyal GroundWater Level ML Forecasting & Quality Prediction System

Final Year Engineering Project — Machine Learning Approach for GroundWater Level Forecasting and Quantity Prediction in Nandyal District, AP (2022–2030).

---

## 🚀 Live Render Deployment Instructions

### Method 1: Automatic Deployment via Render Web Service
1. Log in to [Render.com](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository: `Afroz-ali17/GroundWater_Pred_Nandyal`.
4. Configure the Web Service settings:
   - **Name**: `nandyal-groundwater-ml`
   - **Environment**: `Python 3`
   - **Region**: Any (e.g. Oregon / Singapore)
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt && python run_pipeline.py`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
5. Click **Create Web Service**.
6. Render will automatically build the ML models and host your live website URL (e.g., `https://nandyal-groundwater-ml.onrender.com`)!

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

Open browser at `http://127.0.0.1:5000`.
