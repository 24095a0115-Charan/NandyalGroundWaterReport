import os
import re
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAINWATER_EXCEL_PATH = os.path.join(BASE_DIR, 'NANDYAL Rainwater data.xlsx')
GW_EXCEL_PATH = os.path.join(BASE_DIR, 'NANDYAL GW LEVELS.xlsx')

DEFAULT_MONTHLY_CLIMATOLOGY = {
    1: 3.60, 2: 3.60, 3: 3.60, 4: 3.60,
    5: 51.58, 6: 82.94, 7: 149.18, 8: 127.02,
    9: 138.88, 10: 79.30, 11: 14.70, 12: 3.45
}

def parse_rainfall_data(file_path):
    """
    Parses monthly rainfall amounts (in mm) from the rainwater excel file.
    Handles 'Jan - Apr' combined winter totals and individual monthly observations.
    """
    if not os.path.exists(file_path):
        return {}

    df_raw = pd.read_excel(file_path)
    col = None
    for c in df_raw.columns:
        if 'Rain' in str(c) or 'rain' in str(c):
            col = df_raw[c]
            break
    if col is None and df_raw.shape[1] >= 4:
        col = df_raw.iloc[:, 3]
        
    if col is None:
        return {}
        
    rainfall_records = {}
    current_year = None
    month_names = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    for val in col.dropna():
        s = str(val).strip()
        # Detect 4-digit Year header
        if re.match(r'^(20\d\d)$', s):
            current_year = int(s)
            continue
            
        if current_year is None or 'Annual Total' in s:
            continue
            
        # Match multi-month span e.g., 'Jan – Apr: 18.2 mm'
        m_span = re.search(r'Jan.*?Apr\s*:\s*([\d\.]+)', s, re.I)
        if m_span:
            val_span = float(m_span.group(1))
            for m in [1, 2, 3, 4]:
                rainfall_records[f'{current_year:04d}-{m:02d}-01'] = round(val_span / 4.0, 2)
            continue
            
        # Match single month e.g., 'May: 78.4 mm' or 'Nov (01–02): 0.09 mm'
        m_month = re.search(r'([A-Za-z]{3})(?:\s*\(.*?\))?\s*:\s*([\d\.]+)', s)
        if m_month:
            mon_str = m_month.group(1).lower()
            if mon_str in month_names:
                m_num = month_names[mon_str]
                val_mm = float(m_month.group(2))
                rainfall_records[f'{current_year:04d}-{m_num:02d}-01'] = val_mm
                
    return rainfall_records

def load_nandyal_gw_data(file_path=None):
    """
    Loads and cleans the monthly groundwater level and rainwater data for Nandyal District.
    Returns a cleaned pandas DataFrame indexed by Date with 'WaterLevel_mbgl' and 'Rainfall_mm'.
    """
    if file_path is None:
        if os.path.exists(RAINWATER_EXCEL_PATH):
            file_path = RAINWATER_EXCEL_PATH
        elif os.path.exists('NANDYAL Rainwater data.xlsx'):
            file_path = 'NANDYAL Rainwater data.xlsx'
        elif os.path.exists(GW_EXCEL_PATH):
            file_path = GW_EXCEL_PATH
        elif os.path.exists('NANDYAL GW LEVELS.xlsx'):
            file_path = 'NANDYAL GW LEVELS.xlsx'
        else:
            raise FileNotFoundError("Neither 'NANDYAL Rainwater data.xlsx' nor 'NANDYAL GW LEVELS.xlsx' was found.")

    # Read groundwater level columns
    df_raw = pd.read_excel(file_path, header=1)
    df = df_raw.rename(columns={
        df_raw.columns[0]: 'Date',
        df_raw.columns[1]: 'WaterLevel_mbgl'
    })[['Date', 'WaterLevel_mbgl']].copy()
    
    df['Date'] = pd.to_datetime(df['Date'])
    df['WaterLevel_mbgl'] = pd.to_numeric(df['WaterLevel_mbgl'], errors='coerce')
    df = df.dropna(subset=['Date', 'WaterLevel_mbgl']).sort_values('Date').reset_index(drop=True)
    df.set_index('Date', inplace=True)
    df = df.asfreq('MS')
    
    if df['WaterLevel_mbgl'].isna().sum() > 0:
        df['WaterLevel_mbgl'] = df['WaterLevel_mbgl'].interpolate(method='time')

    # Load rainfall data
    rain_path = RAINWATER_EXCEL_PATH if os.path.exists(RAINWATER_EXCEL_PATH) else file_path
    rain_map = parse_rainfall_data(rain_path)
    
    # Map rainfall to groundwater dates, fallback to climatological monthly average
    rain_values = []
    for d in df.index:
        d_str = d.strftime('%Y-%m-%d')
        if d_str in rain_map:
            rain_values.append(rain_map[d_str])
        else:
            month = d.month
            rain_values.append(DEFAULT_MONTHLY_CLIMATOLOGY.get(month, 20.0))
            
    df['Rainfall_mm'] = np.round(rain_values, 2)
    return df

def get_rainfall_climatology(df=None):
    """
    Returns monthly average rainfall climatology (months 1-12) in mm.
    """
    if df is not None and 'Rainfall_mm' in df.columns:
        climatology = df.groupby(df.index.month)['Rainfall_mm'].mean().to_dict()
        for m in range(1, 13):
            if m not in climatology:
                climatology[m] = DEFAULT_MONTHLY_CLIMATOLOGY.get(m, 20.0)
            else:
                climatology[m] = round(float(climatology[m]), 2)
        return climatology
    return DEFAULT_MONTHLY_CLIMATOLOGY.copy()

if __name__ == '__main__':
    df = load_nandyal_gw_data()
    print("Dataset successfully loaded.")
    print("Shape:", df.shape)
    print("Date Range:", df.index.min().strftime('%Y-%m'), "to", df.index.max().strftime('%Y-%m'))
    print(df.head(10))
    print("Monthly Climatology:", get_rainfall_climatology(df))
