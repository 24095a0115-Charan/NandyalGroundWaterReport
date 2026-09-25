# pyrefly: ignore [missing-import]
import numpy as np

# Nandyal District Parameters (Central Ground Water Board CGWB standard references)
DEFAULT_DISTRICT_AREA_KM2 = 9682.0   # Total geographical area in sq km
DEFAULT_SPECIFIC_YIELD = 0.025       # 2.5% specific yield for Kurnool/Cuddapah series
DEFAULT_MAX_BASELINE_DEPTH_M = 15.0  # Baseline maximum depth reference in meters bgl

def calculate_groundwater_quantity(water_level_mbgl, 
                                   area_sq_km=DEFAULT_DISTRICT_AREA_KM2, 
                                   specific_yield=DEFAULT_SPECIFIC_YIELD,
                                   max_depth_m=DEFAULT_MAX_BASELINE_DEPTH_M):
    """
    Calculates dynamic available groundwater volume in Million Cubic Meters (MCM)
    given current water level depth below ground level (m bgl).
    """
    area_m2 = area_sq_km * 1e6
    head_headroom_m = np.maximum(0.0, max_depth_m - np.array(water_level_mbgl))
    volume_m3 = area_m2 * head_headroom_m * specific_yield
    volume_mcm = volume_m3 / 1e6
    return np.round(volume_mcm, 2)

def calculate_storage_delta(current_mbgl, previous_mbgl,
                            area_sq_km=DEFAULT_DISTRICT_AREA_KM2,
                            specific_yield=DEFAULT_SPECIFIC_YIELD):
    """
    Calculates net storage change in Million Cubic Meters (MCM) between two periods.
    Positive value indicates groundwater recharge / storage addition.
    Negative value indicates groundwater draft / depletion.
    """
    area_m2 = area_sq_km * 1e6
    # Note: previous_mbgl - current_mbgl is positive when water table rises (mbgl decreases)
    delta_h = np.array(previous_mbgl) - np.array(current_mbgl)
    delta_v_mcm = (area_m2 * delta_h * specific_yield) / 1e6
    return np.round(delta_v_mcm, 2)

def get_cgwb_status_zone(water_level_mbgl):
    """
    Returns CGWB Groundwater Exploitation Risk Zone & Hex Color code based on m bgl depth.
    """
    if water_level_mbgl < 5.0:
        return {
            "status": "Safe",
            "category": "High Water Table / Recharged Aquifer",
            "risk_level": "Low",
            "color": "#10b981", # Emerald green
            "badge_class": "badge-safe",
            "recommendation": "Optimal water availability for agriculture & drinking."
        }
    elif water_level_mbgl < 8.0:
        return {
            "status": "Semi-Critical",
            "category": "Moderate Water Table",
            "risk_level": "Moderate",
            "color": "#f59e0b", # Amber/Orange
            "badge_class": "badge-semi-critical",
            "recommendation": "Promote micro-irrigation and seasonal monitoring."
        }
    elif water_level_mbgl < 11.0:
        return {
            "status": "Critical",
            "category": "Deep Water Table / Depletion Risk",
            "risk_level": "High",
            "color": "#f97316", # Deep orange
            "badge_class": "badge-critical",
            "recommendation": "Enforce artificial recharge structures and borewell regulation."
        }
    else:
        return {
            "status": "Over-Exploited",
            "category": "Severe Aquifer Stress / Critical Drawdown",
            "risk_level": "Severe",
            "color": "#ef4444", # Red
            "badge_class": "badge-over-exploited",
            "recommendation": "Emergency water conservation & artificial recharge injection mandatory."
        }

if __name__ == '__main__':
    sample_levels = [4.5, 6.8, 9.5, 12.5]
    for lvl in sample_levels:
        vol = calculate_groundwater_quantity(lvl)
        st = get_cgwb_status_zone(lvl)
        print(f"Level: {lvl} m bgl | Usable Storage: {vol} MCM | Zone: {st['status']}")
