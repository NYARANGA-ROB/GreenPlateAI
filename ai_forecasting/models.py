"""
AI forecasting models for GreenPlateAI.

This module implements machine learning models for predicting
meal demand and food waste using RandomForest and Prophet.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import pickle
import os
from pathlib import Path

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.feature_selection import SelectKBest, f_regression

# Prophet for time series forecasting
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logging.warning("Prophet not available. Install with: pip install prophet")

logger = logging.getLogger(__name__)


class DemandForecastModel:
    """Demand forecasting model using RandomForest and Prophet."""
    
    def __init__(self, model_type: str = "random_forest"):
        """Initialize the forecasting model."""
        self.model_type = model_type.lower()
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_columns = []
        self.target_column = None
        self.is_trained = False
        self.model_metrics = {}
        
        # Model paths
        self.model_dir = Path("models/forecasting")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model based on type
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == "prophet" and PROPHET_AVAILABLE:
            self.model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
                holidays_prior_scale=10,
                mcmc_samples=0,
                interval_width=0.8,
                uncertainty_samples=1000
            )
        else:
            raise ValueError(f"Model type {model_type} not supported")
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for model training."""
        logger.info(f"Preparing features for {len(data)} records")
        
        # Create a copy to avoid modifying original data
        df = data.copy()
        
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Time-based features
        if 'date' in df.columns:
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_month'] = df['date'].dt.day
            df['month'] = df['date'].dt.month
            df['quarter'] = df['date'].dt.quarter
            df['is_weekend'] = df['date'].dt.dayofweek.isin([5, 6]).astype(int)
            df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
            df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        
        # Semester/season features
        if 'month' in df.columns:
            df['semester'] = df['month'].apply(self._get_semester)
            df['season'] = df['month'].apply(self._get_season)
        
        # Encode categorical variables
        categorical_columns = ['dining_hall', 'meal_type', 'category', 'semester', 'season']
        for col in categorical_columns:
            if col in df.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df[col] = self.label_encoders[col].fit_transform(df[col].astype(str))
                else:
                    # Handle unseen categories
                    df[col] = df[col].astype(str)
                    mask = df[col].isin(self.label_encoders[col].classes_)
                    df.loc[mask, col] = self.label_encoders[col].transform(df.loc[mask, col])
                    df.loc[~mask, col] = -1  # Unknown category
        
        # Weather features (if available)
        weather_features = ['temperature', 'humidity', 'precipitation', 'wind_speed']
        for feature in weather_features:
            if feature in df.columns:
                # Fill missing weather data with mean
                df[feature] = df[feature].fillna(df[feature].mean())
        
        # Student population features
        if 'student_count' in df.columns:
            df['student_count'] = df['student_count'].fillna(df['student_count'].mean())
            df['student_per_meal'] = df['student_count'] / df.get('meal_servings', 1)
        
        # Event features
        if 'has_event' in df.columns:
            df['has_event'] = df['has_event'].fillna(0).astype(int)
        
        # Lag features (for time series)
        if self.model_type == "random_forest":
            df = self._create_lag_features(df)
        
        # Rolling features
        if self.model_type == "random_forest":
            df = self._create_rolling_features(df)
        
        logger.info(f"Prepared {len(df.columns)} features")
        return df
    
    def _get_semester(self, month: int) -> str:
        """Get semester from month."""
        if month in [1, 2, 3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        elif month in [9, 10, 11, 12]:
            return "Fall"
        else:
            return "Unknown"
    
    def _get_season(self, month: int) -> str:
        """Get season from month."""
        if month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"
    
    def _create_lag_features(self, df: pd.DataFrame, lags: List[int] = None) -> pd.DataFrame:
        """Create lag features for time series."""
        if lags is None:
            lags = [1, 2, 3, 7, 14]  # Previous day, 2 days ago, 3 days ago, last week, 2 weeks ago
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Create lag features for target column
        target_col = 'demand' if 'demand' in df.columns else 'quantity'
        if target_col in df.columns:
            for lag in lags:
                df[f'{target_col}_lag_{lag}'] = df[target_col].shift(lag)
        
        return df
    
    def _create_rolling_features(self, df: pd.DataFrame, windows: List[int] = None) -> pd.DataFrame:
        """Create rolling window features."""
        if windows is None:
            windows = [3, 7, 14]  # 3-day, 7-day, 14-day windows
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Create rolling features for target column
        target_col = 'demand' if 'demand' in df.columns else 'quantity'
        if target_col in df.columns:
            for window in windows:
                df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window).mean()
                df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window).std()
                df[f'{target_col}_rolling_min_{window}'] = df[target_col].rolling(window).min()
                df[f'{target_col}_rolling_max_{window}'] = df[target_col].rolling(window).max()
        
        return df
    
    def train(self, data: pd.DataFrame, target_column: str, test_size: float = 0.2) -> Dict[str, Any]:
        """Train the forecasting model."""
        logger.info(f"Training {self.model_type} model for {target_column}")
        
        # Prepare features
        df = self.prepare_features(data)
        
        # Store target column
        self.target_column = target_column
        
        # Remove rows with missing target
        df = df.dropna(subset=[target_column])
        
        # Prepare features and target
        if self.model_type == "prophet":
            # Prophet requires specific format
            prophet_df = df[['date', target_column]].copy()
            prophet_df.columns = ['ds', 'y']
            
            # Split data
            train_size = int(len(prophet_df) * (1 - test_size))
            train_df = prophet_df[:train_size]
            test_df = prophet_df[train_size:]
            
            # Train model
            self.model.fit(train_df)
            
            # Make predictions
            forecast = self.model.predict(test_df)
            
            # Calculate metrics
            y_true = test_df['y'].values
            y_pred = forecast['yhat'].values[:len(y_true)]
            
        else:
            # RandomForest
            # Select feature columns (exclude target and date)
            exclude_columns = [target_column, 'date']
            self.feature_columns = [col for col in df.columns if col not in exclude_columns]
            
            # Remove rows with missing features
            df = df.dropna(subset=self.feature_columns)
            
            X = df[self.feature_columns]
            y = df[target_column]
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model.fit(X_train_scaled, y_train)
            
            # Make predictions
            y_pred = self.model.predict(X_test_scaled)
            y_true = y_test.values
        
        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
        
        self.model_metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape,
            'model_type': self.model_type,
            'training_samples': len(X_train) if self.model_type == "random_forest" else len(train_df),
            'test_samples': len(X_test) if self.model_type == "random_forest" else len(test_df),
            'feature_count': len(self.feature_columns) if self.model_type == "random_forest" else 0
        }
        
        self.is_trained = True
        
        logger.info(f"Model trained. MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.3f}")
        
        return self.model_metrics
    
    def predict(self, data: pd.DataFrame, horizon: int = 1) -> Dict[str, Any]:
        """Make predictions using the trained model."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        logger.info(f"Making {self.model_type} predictions for {horizon} periods")
        
        # Prepare features
        df = self.prepare_features(data)
        
        if self.model_type == "prophet":
            # Prophet requires specific format
            prophet_df = df[['date']].copy()
            prophet_df.columns = ['ds']
            
            # Make future dataframe
            future = self.model.make_future_dataframe(periods=horizon)
            
            # Make predictions
            forecast = self.model.predict(future)
            
            # Extract predictions
            predictions = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(horizon)
            
            return {
                'predictions': predictions['yhat'].values,
                'lower_bound': predictions['yhat_lower'].values,
                'upper_bound': predictions['yhat_upper'].values,
                'dates': predictions['ds'].values,
                'model_type': self.model_type
            }
        
        else:
            # RandomForest
            # Ensure we have the required features
            missing_features = set(self.feature_columns) - set(df.columns)
            if missing_features:
                for feature in missing_features:
                    df[feature] = 0  # Fill missing features with 0
            
            X = df[self.feature_columns]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            predictions = self.model.predict(X_scaled)
            
            # For multiple predictions, we'll predict for the next few periods
            if horizon > 1:
                # Use the last available data for future predictions
                last_features = X_scaled[-1:]
                future_predictions = []
                
                for i in range(horizon):
                    pred = self.model.predict(last_features)[0]
                    future_predictions.append(pred)
                
                return {
                    'predictions': np.array(future_predictions),
                    'model_type': self.model_type
                }
            else:
                return {
                    'predictions': predictions,
                    'model_type': self.model_type
                }
    
    def evaluate(self, data: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """Evaluate model performance."""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        logger.info(f"Evaluating {self.model_type} model")
        
        # Prepare features
        df = self.prepare_features(data)
        
        if self.model_type == "prophet":
            # Prophet evaluation
            prophet_df = df[['date', target_column]].copy()
            prophet_df.columns = ['ds', 'y']
            
            # Make predictions
            forecast = self.model.predict(prophet_df)
            
            # Calculate metrics
            y_true = prophet_df['y'].values
            y_pred = forecast['yhat'].values
            
        else:
            # RandomForest evaluation
            exclude_columns = [target_column, 'date']
            X = df[self.feature_columns]
            y = df[target_column]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            y_pred = self.model.predict(X_scaled)
            y_true = y.values
        
        # Calculate metrics
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-8))) * 100
        
        evaluation_metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2': r2,
            'mape': mape,
            'model_type': self.model_type,
            'sample_count': len(y_true)
        }
        
        logger.info(f"Model evaluation. MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {r2:.3f}")
        
        return evaluation_metrics
    
    def save_model(self, filename: str = None) -> str:
        """Save the trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.model_type}_{self.target_column}_{timestamp}.pkl"
        
        filepath = self.model_dir / filename
        
        # Save model and metadata
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'target_column': self.target_column,
            'model_type': self.model_type,
            'metrics': self.model_metrics,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
        return str(filepath)
    
    def load_model(self, filepath: str) -> bool:
        """Load a trained model from disk."""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_columns = model_data['feature_columns']
            self.target_column = model_data['target_column']
            self.model_type = model_data['model_type']
            self.model_metrics = model_data['metrics']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance for RandomForest models."""
        if self.model_type != "random_forest" or not self.is_trained:
            return None
        
        importance = self.model.feature_importances_
        feature_names = self.feature_columns
        
        return dict(zip(feature_names, importance))


class WasteForecastModel(DemandForecastModel):
    """Specialized model for food waste forecasting."""
    
    def __init__(self, model_type: str = "random_forest"):
        """Initialize waste forecasting model."""
        super().__init__(model_type)
        self.waste_categories = None
        self.category_models = {}
    
    def train_category_models(self, data: pd.DataFrame, target_column: str = "quantity") -> Dict[str, Any]:
        """Train separate models for each waste category."""
        logger.info("Training category-specific waste models")
        
        # Get unique categories
        self.waste_categories = data['category'].unique()
        category_metrics = {}
        
        for category in self.waste_categories:
            logger.info(f"Training model for category: {category}")
            
            # Filter data for this category
            category_data = data[data['category'] == category].copy()
            
            if len(category_data) < 10:  # Skip categories with insufficient data
                logger.warning(f"Insufficient data for category {category}: {len(category_data)} records")
                continue
            
            # Create and train model for this category
            category_model = DemandForecastModel(self.model_type)
            metrics = category_model.train(category_data, target_column)
            
            # Store model
            self.category_models[category] = category_model
            category_metrics[category] = metrics
        
        return category_metrics
    
    def predict_category_waste(self, data: pd.DataFrame, category: str, horizon: int = 1) -> Dict[str, Any]:
        """Predict waste for specific category."""
        if category not in self.category_models:
            raise ValueError(f"No model trained for category: {category}")
        
        return self.category_models[category].predict(data, horizon)
    
    def predict_total_waste(self, data: pd.DataFrame, horizon: int = 1) -> Dict[str, Any]:
        """Predict total waste across all categories."""
        total_predictions = []
        category_predictions = {}
        
        for category, model in self.category_models.items():
            try:
                pred = model.predict(data, horizon)
                category_predictions[category] = pred
                
                if isinstance(pred['predictions'], np.ndarray):
                    total_predictions.append(pred['predictions'])
                else:
                    total_predictions.append([pred['predictions']])
            except Exception as e:
                logger.error(f"Error predicting for category {category}: {str(e)}")
                category_predictions[category] = {'predictions': np.array([0])}
        
        # Sum predictions across categories
        if total_predictions:
            total_predictions = np.sum(total_predictions, axis=0)
        else:
            total_predictions = np.array([0])
        
        return {
            'total_predictions': total_predictions,
            'category_predictions': category_predictions,
            'model_type': self.model_type
        }


class EnsembleForecastModel:
    """Ensemble model combining multiple forecasting approaches."""
    
    def __init__(self, models: List[str] = None):
        """Initialize ensemble model."""
        if models is None:
            models = ["random_forest", "prophet"] if PROPHET_AVAILABLE else ["random_forest"]
        
        self.models = {}
        self.weights = {}
        self.is_trained = False
        
        # Initialize models
        for model_type in models:
            try:
                self.models[model_type] = DemandForecastModel(model_type)
                self.weights[model_type] = 1.0 / len(models)
            except Exception as e:
                logger.error(f"Error initializing model {model_type}: {str(e)}")
    
    def train(self, data: pd.DataFrame, target_column: str, test_size: float = 0.2) -> Dict[str, Any]:
        """Train all models in the ensemble."""
        logger.info("Training ensemble model")
        
        ensemble_metrics = {}
        
        for model_name, model in self.models.items():
            try:
                metrics = model.train(data, target_column, test_size)
                ensemble_metrics[model_name] = metrics
            except Exception as e:
                logger.error(f"Error training model {model_name}: {str(e)}")
        
        # Calculate weights based on model performance (inverse of MAE)
        total_inverse_mae = sum(1 / metrics['mae'] for metrics in ensemble_metrics.values() if metrics['mae'] > 0)
        
        for model_name in self.models:
            if model_name in ensemble_metrics and ensemble_metrics[model_name]['mae'] > 0:
                self.weights[model_name] = (1 / ensemble_metrics[model_name]['mae']) / total_inverse_mae
            else:
                self.weights[model_name] = 0
        
        self.is_trained = True
        
        logger.info(f"Ensemble trained with weights: {self.weights}")
        
        return {
            'ensemble_metrics': ensemble_metrics,
            'model_weights': self.weights,
            'is_trained': self.is_trained
        }
    
    def predict(self, data: pd.DataFrame, horizon: int = 1) -> Dict[str, Any]:
        """Make ensemble predictions."""
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before making predictions")
        
        logger.info(f"Making ensemble predictions for {horizon} periods")
        
        predictions = {}
        
        for model_name, model in self.models.items():
            try:
                pred = model.predict(data, horizon)
                predictions[model_name] = pred
            except Exception as e:
                logger.error(f"Error predicting with model {model_name}: {str(e)}")
        
        # Combine predictions using weights
        ensemble_predictions = None
        total_weight = 0
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 0)
            if weight > 0 and isinstance(pred['predictions'], np.ndarray):
                if ensemble_predictions is None:
                    ensemble_predictions = pred['predictions'] * weight
                else:
                    ensemble_predictions += pred['predictions'] * weight
                total_weight += weight
        
        if total_weight > 0:
            ensemble_predictions /= total_weight
        
        return {
            'ensemble_predictions': ensemble_predictions,
            'individual_predictions': predictions,
            'model_weights': self.weights
        }
