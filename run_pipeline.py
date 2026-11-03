import os
import json
import pandas as pd

from src.data_loader import load_nandyal_gw_data, get_rainfall_climatology
from src.feature_engineering import create_time_series_features, prepare_train_test_data
from src.models import GroundwaterMLSuite, recursive_multi_step_forecast
from src.quantity_calculator import (
    calculate_groundwater_quantity, 
    calculate_storage_delta, 
    get_cgwb_status_zone,
    calculate_rainfall_gw_relationship
)
from src.water_quality import estimate_nandyal_water_quality, calculate_wqi
from src.evaluate import evaluate_models_time_series_split

def run_groundwater_ml_pipeline():
    print("=========================================================")
    print("Starting Nandyal GroundWater Level & Rainfall ML Pipeline Execution...")
    print("Models: Random Forest, SVM, Decision Tree & Ensemble")
    print("Extended Multi-Step Horizon Forecasting up to Dec 2030")
    print("=========================================================")
    
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    # 1. Load Data (Groundwater levels and rainfall observations)
    df = load_nandyal_gw_data()
    climatology = get_rainfall_climatology(df)
    
    # 2. Evaluate Empirical Link between Rainfall and Groundwater
    rainfall_gw_link = calculate_rainfall_gw_relationship(df)
    print(f"Rainfall-GW Storage Correlation: {rainfall_gw_link.get('seasonal_recharge_correlation', 'N/A')}")
    print(f"Annual Average Rainfall: {rainfall_gw_link.get('annual_average_rainfall_mm', 'N/A')} mm")
    
    # 3. Feature Engineering with Rainfall Infiltration Features
    df_feat = create_time_series_features(df)
    X, y, feature_cols = prepare_train_test_data(df_feat)
    
    # 4. Train Machine Learning Models (RF, SVM, DT, Ensemble)
    ml_suite = GroundwaterMLSuite()
    ml_suite.train_all_models(X, y, feature_cols)
    
    # 5. Evaluate Benchmark Metrics
    benchmark_metrics = evaluate_models_time_series_split(df_feat, ml_suite, test_months=10)
    
    # 6. Generate Extended 52-Month Future Multi-Step Forecast (2026-09 to 2030-12)
    FORECAST_HORIZON_MONTHS = 52
    forecast_df = recursive_multi_step_forecast(
        df, 
        ml_suite, 
        forecast_horizon=FORECAST_HORIZON_MONTHS,
        rainfall_climatology=climatology
    )
    
    print(f"Generated {FORECAST_HORIZON_MONTHS}-month forecast from {forecast_df['Date'].min().strftime('%Y-%m')} to {forecast_df['Date'].max().strftime('%Y-%m')}.")
    
    # 7. Format Historical Data with Quantities, Rainfall & Water Quality Assessment (WQI)
    historical_records = []
    prev_level = None
    for date, row in df.iterrows():
        lvl = float(row['WaterLevel_mbgl'])
        rain_mm = float(row.get('Rainfall_mm', 0.0))
        date_str = date.strftime('%Y-%m-%d')
        vol_mcm = float(calculate_groundwater_quantity(lvl))
        status_info = get_cgwb_status_zone(lvl)
        delta_mcm = float(calculate_storage_delta(lvl, prev_level)) if prev_level is not None else 0.0
        prev_level = lvl
        
        wq_params = estimate_nandyal_water_quality(lvl)
        wqi_info = calculate_wqi(wq_params)
        
        historical_records.append({
            'date': date_str,
            'month': date.strftime('%b %Y'),
            'water_level_mbgl': round(lvl, 3),
            'rainfall_mm': round(rain_mm, 2),
            'quantity_mcm': vol_mcm,
            'storage_delta_mcm': delta_mcm,
            'status': status_info['status'],
            'category': status_info['category'],
            'color': status_info['color'],
            'water_quality': wq_params,
            'wqi': wqi_info['wqi'],
            'wqi_status': wqi_info['status']
        })
        
    # 8. Format Extended Forecast Data up to 2030 with Projected Rainfall
    forecast_records = []
    prev_fc_level = historical_records[-1]['water_level_mbgl']
    for idx, row in forecast_df.iterrows():
        fc_date = row['Date']
        date_str = fc_date.strftime('%Y-%m-%d')
        month_str = fc_date.strftime('%b %Y')
        ens_lvl = float(row['Ensemble'])
        rain_mm = float(row.get('Rainfall_mm', 0.0))
        vol_mcm = float(calculate_groundwater_quantity(ens_lvl))
        status_info = get_cgwb_status_zone(ens_lvl)
        delta_mcm = float(calculate_storage_delta(ens_lvl, prev_fc_level))
        prev_fc_level = ens_lvl
        
        wq_params = estimate_nandyal_water_quality(ens_lvl)
        wqi_info = calculate_wqi(wq_params)
        
        forecast_records.append({
            'date': date_str,
            'month': month_str,
            'rainfall_mm': round(rain_mm, 2),
            'RandomForest': float(row['RandomForest']),
            'SVM': float(row['SVM']),
            'DecisionTree': float(row['DecisionTree']),
            'Ensemble': float(ens_lvl),
            'Upper_Bound': float(row['Upper_Bound']),
            'Lower_Bound': float(row['Lower_Bound']),
            'quantity_mcm': vol_mcm,
            'storage_delta_mcm': delta_mcm,
            'status': status_info['status'],
            'category': status_info['category'],
            'color': status_info['color'],
            'water_quality': wq_params,
            'wqi': wqi_info['wqi'],
            'wqi_status': wqi_info['status']
        })
        
    latest_hist = historical_records[-1]
    
    district_summary = {
        'district_name': 'Nandyal District, AP',
        'latest_reading_date': latest_hist['month'],
        'latest_water_level_mbgl': latest_hist['water_level_mbgl'],
        'latest_rainfall_mm': latest_hist['rainfall_mm'],
        'latest_quantity_mcm': latest_hist['quantity_mcm'],
        'latest_wqi': latest_hist['wqi'],
        'latest_wqi_status': latest_hist['wqi_status'],
        'status': latest_hist['status'],
        'category': latest_hist['category'],
        'color': latest_hist['color'],
        'total_area_km2': 9682.0,
        'specific_yield': 0.025,
        'total_historical_months': len(historical_records),
        'forecast_horizon_months': FORECAST_HORIZON_MONTHS,
        'forecast_end_date': forecast_records[-1]['month'],
        'rainfall_gw_link': rainfall_gw_link,
        'climatology': climatology
    }
    
    output_payload = {
        'summary': district_summary,
        'benchmark_metrics': benchmark_metrics,
        'historical': historical_records,
        'forecast': forecast_records
    }
    
    with open('data/processed_results.json', 'w') as f:
        json.dump(output_payload, f, indent=2)
        
    print("Extended forecast pipeline finished successfully!")
    return output_payload

if __name__ == '__main__':
    run_groundwater_ml_pipeline()
