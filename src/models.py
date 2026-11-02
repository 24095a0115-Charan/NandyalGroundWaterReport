# pyrefly: ignore [missing-import]
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

class GroundwaterMLSuite:
    def __init__(self):
        self.scalers = {}
        self.models = {}
        self.feature_cols = []
        self.is_trained = False

    def train_all_models(self, X_train, y_train, feature_cols):
        """
        Trains the Machine Learning models:
        Random Forest (RF), Support Vector Machine (SVM), Decision Tree (DT), 
        and Weighted Ensemble.
        """
        self.feature_cols = list(feature_cols)
        
        # 1. Random Forest (RF)
        rf = RandomForestRegressor(
            n_estimators=100,
            max_depth=4,
            random_state=42
        )
        rf.fit(X_train, y_train)
        self.models['RandomForest'] = rf

        # 2. Support Vector Machine / SVR (SVM)
        scaler_X = StandardScaler()
        scaler_y = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        y_train_scaled = scaler_y.fit_transform(y_train.values.reshape(-1, 1)).ravel()
        
        svm = SVR(kernel='rbf', C=10.0, epsilon=0.1)
        svm.fit(X_train_scaled, y_train_scaled)
        
        self.scalers['SVM_X'] = scaler_X
        self.scalers['SVM_y'] = scaler_y
        self.models['SVM'] = svm
        
        # 3. Decision Tree (DT)
        dt = DecisionTreeRegressor(
            max_depth=4,
            min_samples_split=3,
            random_state=42
        )
        dt.fit(X_train, y_train)
        self.models['DecisionTree'] = dt
        
        self.is_trained = True

    def predict(self, model_name, X):
        """
        Predicts using a specified trained model architecture.
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found.")
            
        if model_name == 'SVM':
            X_scaled = self.scalers['SVM_X'].transform(X)
            y_pred_scaled = self.models['SVM'].predict(X_scaled)
            return self.scalers['SVM_y'].inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
        else:
            return self.models[model_name].predict(X)

    def predict_ensemble(self, X, weights={'RandomForest': 0.45, 'SVM': 0.35, 'DecisionTree': 0.20}):
        """
        Calculates weighted ensemble prediction across RF, SVM, and Decision Tree.
        """
        preds = np.zeros(len(X))
        for m_name, w in weights.items():
            preds += w * self.predict(m_name, X)
        return preds


def recursive_multi_step_forecast(df_historical, ml_suite, forecast_horizon=12, target_col='WaterLevel_mbgl'):
    """
    Generates multi-step future recursive predictions up to forecast_horizon months.
    Updates RF, SVM, DT, and Ensemble predictions.
    """
    df_forecast = df_historical.copy()
    last_date = df_forecast.index[-1]
    
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, forecast_horizon + 1)]
    
    rf_forecasts = []
    svm_forecasts = []
    dt_forecasts = []
    ensemble_forecasts = []
    upper_bounds = []
    lower_bounds = []
    
    working_series = df_historical[target_col].copy()
    
    for i, date in enumerate(future_dates):
        month = date.month
        year = date.year
        quarter = date.quarter
        
        feat_dict = {}
        feat_dict['Month'] = month
        feat_dict['Quarter'] = quarter
        feat_dict['Year'] = year
        feat_dict['Month_Sin'] = np.sin(2 * np.pi * month / 12.0)
        feat_dict['Month_Cos'] = np.cos(2 * np.pi * month / 12.0)
        feat_dict['Is_Monsoon'] = 1 if month in [6, 7, 8, 9, 10, 11] else 0
        feat_dict['Is_Pre_Monsoon'] = 1 if month in [3, 4, 5] else 0
        
        feat_dict['lag_1'] = working_series.iloc[-1]
        feat_dict['lag_2'] = working_series.iloc[-2] if len(working_series) >= 2 else working_series.iloc[-1]
        feat_dict['lag_3'] = working_series.iloc[-3] if len(working_series) >= 3 else working_series.iloc[-1]
        feat_dict['lag_12'] = working_series.iloc[-12] if len(working_series) >= 12 else working_series.iloc[-1]
        
        feat_dict['diff_1'] = working_series.iloc[-1] - working_series.iloc[-2] if len(working_series) >= 2 else 0.0
        
        feat_dict['rolling_mean_3'] = working_series.iloc[-3:].mean()
        feat_dict['rolling_std_3'] = working_series.iloc[-3:].std() if len(working_series) >= 3 else 0.0
        feat_dict['rolling_mean_6'] = working_series.iloc[-6:].mean()
        feat_dict['rolling_std_6'] = working_series.iloc[-6:].std() if len(working_series) >= 6 else 0.0
        feat_dict['rolling_min_6'] = working_series.iloc[-6:].min()
        feat_dict['rolling_max_6'] = working_series.iloc[-6:].max()
        
        X_step = pd.DataFrame([feat_dict])[ml_suite.feature_cols]
        
        pred_rf = float(ml_suite.predict('RandomForest', X_step)[0])
        pred_svm = float(ml_suite.predict('SVM', X_step)[0])
        pred_dt = float(ml_suite.predict('DecisionTree', X_step)[0])
        pred_ens = float(ml_suite.predict_ensemble(X_step)[0])
        
        preds_arr = [pred_rf, pred_svm, pred_dt]
        std_err = np.std(preds_arr) + 0.12 * (i + 1)**0.5
        
        rf_forecasts.append(pred_rf)
        svm_forecasts.append(pred_svm)
        dt_forecasts.append(pred_dt)
        ensemble_forecasts.append(pred_ens)
        upper_bounds.append(pred_ens + 1.96 * std_err)
        lower_bounds.append(max(1.0, pred_ens - 1.96 * std_err))
        
        working_series.loc[date] = pred_ens

    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'RandomForest': np.round(rf_forecasts, 4),
        'SVM': np.round(svm_forecasts, 4),
        'DecisionTree': np.round(dt_forecasts, 4),
        'Ensemble': np.round(ensemble_forecasts, 4),
        'Upper_Bound': np.round(upper_bounds, 4),
        'Lower_Bound': np.round(lower_bounds, 4)
    })
    
    return forecast_df

