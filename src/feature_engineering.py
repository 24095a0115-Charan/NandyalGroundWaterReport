import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np


def create_time_series_features(df, target_col='WaterLevel_mbgl', lags=[1, 2, 3, 12]):
    """
    Creates feature set for time-series Machine Learning models.
    """
    data = df.copy()
    
    # Extract temporal features
    data['Month'] = data.index.month
    data['Quarter'] = data.index.quarter
    data['Year'] = data.index.year
    
    # Cyclical Month encoding
    data['Month_Sin'] = np.sin(2 * np.pi * data['Month'] / 12.0)
    data['Month_Cos'] = np.cos(2 * np.pi * data['Month'] / 12.0)
    
    # Monsoon season indicator for Nandyal (South-West & North-East monsoon: Jun-Nov)
    data['Is_Monsoon'] = data['Month'].isin([6, 7, 8, 9, 10, 11]).astype(int)
    data['Is_Pre_Monsoon'] = data['Month'].isin([3, 4, 5]).astype(int)
    
    # Create Lag features
    for lag in lags:
        data[f'lag_{lag}'] = data[target_col].shift(lag)
        
    # 1-month difference (Water level delta)
    data['diff_1'] = data[target_col].shift(1) - data[target_col].shift(2)
    
    # Rolling statistics
    data['rolling_mean_3'] = data[target_col].shift(1).rolling(window=3).mean()
    data['rolling_std_3'] = data[target_col].shift(1).rolling(window=3).std()
    data['rolling_mean_6'] = data[target_col].shift(1).rolling(window=6).mean()
    data['rolling_std_6'] = data[target_col].shift(1).rolling(window=6).std()
    data['rolling_min_6'] = data[target_col].shift(1).rolling(window=6).min()
    data['rolling_max_6'] = data[target_col].shift(1).rolling(window=6).max()
    
    return data

def prepare_train_test_data(df_features, target_col='WaterLevel_mbgl', drop_na=True):
    """
    Splits features and target variable.
    """
    if drop_na:
        data = df_features.dropna()
    else:
        data = df_features.copy()
        
    feature_cols = [c for c in data.columns if c not in [target_col]]
    X = data[feature_cols]
    y = data[target_col]
    
    return X, y, feature_cols

if __name__ == '__main__':
    from data_loader import load_nandyal_gw_data
    df = load_nandyal_gw_data()
    df_feat = create_time_series_features(df)
    X, y, feature_cols = prepare_train_test_data(df_feat)
    print("Features engineered successfully.")
    print("Feature columns count:", len(feature_cols))
    print("Clean rows for training:", len(X))
    print(X.tail())
