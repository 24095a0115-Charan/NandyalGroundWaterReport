import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_EXCEL_PATH = os.path.join(BASE_DIR, 'NANDYAL GW LEVELS.xlsx')

def load_nandyal_gw_data(file_path=None):
    """
    Loads and cleans the monthly groundwater level data for Nandyal District.
    Dynamically locates 'NANDYAL GW LEVELS.xlsx' relative to project root.
    Returns a cleaned pandas DataFrame indexed by Date with 'WaterLevel_mbgl' column.
    """
    if file_path is None:
        file_path = DEFAULT_EXCEL_PATH
        
    if not os.path.exists(file_path):
        # Fallback check in current working directory
        if os.path.exists('NANDYAL GW LEVELS.xlsx'):
            file_path = 'NANDYAL GW LEVELS.xlsx'
        else:
            raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    # Read excel file skipping header row if needed
    df_raw = pd.read_excel(file_path, header=1)
    
    # Standardize column names
    df = df_raw.rename(columns={
        df_raw.columns[0]: 'Date',
        df_raw.columns[1]: 'WaterLevel_mbgl'
    })
    
    # Ensure Date is datetime and sorted
    df['Date'] = pd.to_datetime(df['Date'])
    df['WaterLevel_mbgl'] = pd.to_numeric(df['WaterLevel_mbgl'], errors='coerce')
    
    # Drop invalid rows and sort chronologically
    df = df.dropna(subset=['Date', 'WaterLevel_mbgl']).sort_values('Date').reset_index(drop=True)
    
    # Set frequency to Monthly Start (MS)
    df.set_index('Date', inplace=True)
    df = df.asfreq('MS')
    
    # Interpolate if any missing dates exist
    if df['WaterLevel_mbgl'].isna().sum() > 0:
        df['WaterLevel_mbgl'] = df['WaterLevel_mbgl'].interpolate(method='time')
        
    return df

if __name__ == '__main__':
    df = load_nandyal_gw_data()
    print("Dataset successfully loaded.")
    print("Shape:", df.shape)
    print("Date Range:", df.index.min().strftime('%Y-%m'), "to", df.index.max().strftime('%Y-%m'))
    print(df.head())
