import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

def calculate_metrics(y_true, y_pred):
    """
    Computes RMSE, MAE, R2, and MAPE metrics between true and predicted targets.
    """
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae = float(mean_absolute_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    
    nonzero_idx = y_true != 0
    mape = float(np.mean(np.abs((y_true[nonzero_idx] - y_pred[nonzero_idx]) / y_true[nonzero_idx])) * 100)
    
    return {
        'RMSE': round(rmse, 4),
        'MAE': round(mae, 4),
        'R2': round(r2, 4),
        'MAPE': round(mape, 2)
    }

def evaluate_models_time_series_split(df_features, ml_suite, target_col='WaterLevel_mbgl', test_months=10):
    """
    Evaluates RF, SVM, DT, and Ensemble models using time-series train/test split.
    """
    data = df_features.dropna().copy()
    
    train_data = data.iloc[:-test_months]
    test_data = data.iloc[-test_months:]
    
    X_train = train_data[ml_suite.feature_cols]
    y_train = train_data[target_col]
    
    X_test = test_data[ml_suite.feature_cols]
    y_test = test_data[target_col]
    
    test_ml_suite = type(ml_suite)()
    test_ml_suite.train_all_models(X_train, y_train, ml_suite.feature_cols)
    
    results = {}
    
    for m_name in list(test_ml_suite.models.keys()):
        preds = test_ml_suite.predict(m_name, X_test)
        results[m_name] = calculate_metrics(y_test, preds)
        
    ens_preds = test_ml_suite.predict_ensemble(X_test)
    results['Ensemble'] = calculate_metrics(y_test, ens_preds)
    
    return results

