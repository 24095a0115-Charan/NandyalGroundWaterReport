# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd

# WHO & BIS (IS 10500:2012) Drinking Water Standards for Nandyal Hydrogeological Region
WATER_QUALITY_STANDARDS = {
    'pH': {'ideal': 7.0, 'standard': 8.5, 'weight': 4},
    'EC': {'ideal': 300.0, 'standard': 1500.0, 'weight': 3},  # uS/cm
    'TDS': {'ideal': 200.0, 'standard': 500.0, 'weight': 4},   # mg/L
    'Nitrate': {'ideal': 0.0, 'standard': 45.0, 'weight': 5},  # mg/L (NO3-)
    'Fluoride': {'ideal': 1.0, 'standard': 1.5, 'weight': 5}   # mg/L (F-)
}

def estimate_nandyal_water_quality(water_level_mbgl, rainfall_anomaly_pct=0.0):
    """
    Estimates water quality parameters (pH, EC, TDS, Nitrate, Fluoride) for Nandyal District
    based on water level depth and recharge anomaly. Deep water levels increase mineral concentration.
    """
    depth_factor = (water_level_mbgl - 5.0) / 10.0  # Normalized depth effect
    recharge_dilution = 1.0 - (rainfall_anomaly_pct / 100.0) * 0.15
    
    # Baseline values adjusted for hydrogeology
    ph = round(7.3 + 0.3 * np.clip(depth_factor, -0.5, 1.0), 2)
    ec = round(950 + 400 * depth_factor * recharge_dilution, 1)        # uS/cm
    tds = round(580 + 320 * depth_factor * recharge_dilution, 1)       # mg/L
    nitrate = round(28 + 18 * depth_factor * recharge_dilution, 1)     # mg/L
    fluoride = round(1.15 + 0.45 * depth_factor * recharge_dilution, 2)# mg/L
    
    return {
        'pH': ph,
        'EC': ec,
        'TDS': tds,
        'Nitrate': nitrate,
        'Fluoride': fluoride
    }

def calculate_wqi(quality_dict):
    """
    Calculates Weighted Arithmetic Water Quality Index (WQI).
    """
    sum_weights = sum(s['weight'] for s in WATER_QUALITY_STANDARDS.values())
    wqi_sum = 0.0
    
    param_statuses = {}
    
    for param, val in quality_dict.items():
        std_info = WATER_QUALITY_STANDARDS[param]
        w = std_info['weight'] / sum_weights
        
        if param == 'pH':
            q = abs(val - 7.0) / (8.5 - 7.0) * 100
        else:
            q = (val / std_info['standard']) * 100
            
        wqi_sum += w * q
        
        # Parameter safety check
        is_safe = val <= std_info['standard'] if param != 'pH' else (6.5 <= val <= 8.5)
        param_statuses[param] = {
            'value': val,
            'standard': std_info['standard'],
            'is_safe': is_safe
        }
        
    wqi = round(wqi_sum, 2)
    
    # Classify WQI
    if wqi < 50:
        category = "Excellent Quality (Safe for Drinking)"
        status = "Safe"
        color = "#10b981" # Green
    elif wqi < 100:
        category = "Good Quality (Suitable for Drinking & Ag)"
        status = "Good"
        color = "#06b6d4" # Cyan
    elif wqi < 150:
        category = "Poor Quality (Requires Filtration)"
        status = "Poor"
        color = "#f59e0b" # Amber
    elif wqi < 200:
        category = "Very Poor Quality (High TDS / Fluoride Risk)"
        status = "Very Poor"
        color = "#f97316" # Orange
    else:
        category = "Unsuitable for Drinking (Severe Contamination)"
        status = "Critical Contamination"
        color = "#ef4444" # Red

    return {
        'wqi': wqi,
        'status': status,
        'category': category,
        'color': color,
        'parameters': param_statuses
    }

if __name__ == '__main__':
    sample_depths = [4.5, 7.5, 11.5]
    for d in sample_depths:
        q_dict = estimate_nandyal_water_quality(d)
        wqi_res = calculate_wqi(q_dict)
        print(f"Depth {d}m bgl -> WQI: {wqi_res['wqi']} ({wqi_res['status']}) | Fluoride: {q_dict['Fluoride']} mg/L")
