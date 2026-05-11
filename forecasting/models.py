"""
Machine learning models for forecasting in GreenPlateAI.

This module provides functions for demand forecasting, waste prediction,
and model management using various ML algorithms.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
import pickle
import os
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
try:
    import xgboost as xgb
except ImportError:
    xgb = None
try:
    import lightgbm as lgb
except ImportError:
    lgb = None

from database.connection import get_session
from models.waste_record import WasteRecord
from models.prediction import Prediction, PredictionModel, PredictionType, ModelMetrics
from models.food_item import FoodItem
from utils.config import get_config
from utils.helpers import convert_to_utc

logger = logging.getLogger(__name__)

# Model registry
MODEL_CLASSES = {
    'linear_regression': LinearRegression,
    'random_forest': RandomForestRegressor,
    'gradient_boosting': GradientBoostingRegressor,
}

if xgb is not None:
    MODEL_CLASSES['xgboost'] = xgb.XGBRegressor
if lgb is not None:
    MODEL_CLASSES['lightgbm'] = lgb.LGBMRegressor


def get_demand_forecast(
    days_ahead: int = 7,
    meal_period: str = None,
    dining_hall: str = None,
    food_item_id: int = None,
    model_type: str = 'xgboost'
) -> List[Dict[str, Any]]:
    """
    Generate demand forecast for the specified period.
    
    Args:
        days_ahead: Number of days to forecast
        meal_period: Specific meal period to forecast
        dining_hall: Specific dining hall to forecast
        food_item_id: Specific food item to forecast
        model_type: ML model type to use
        
    Returns:
        list: Forecast data with dates and predictions
    """
    try:
        # Load the appropriate model
        model = load_demand_model(model_type)
        if model is None:
            logger.warning(f"No trained model available for {model_type}, using fallback")
            return generate_fallback_forecast(days_ahead, meal_period, dining_hall)
        
        # Generate future dates
        forecast_dates = []
        base_date = date.today()
        
        for i in range(days_ahead):
            forecast_date = base_date + timedelta(days=i+1)
            forecast_dates.append(forecast_date)
        
        # Extract features for each date
        forecasts = []
        
        for forecast_date in forecast_dates:
            # Create feature vector
            features = extract_forecast_features(
                forecast_date, meal_period, dining_hall, food_item_id
            )
            
            if features is None:
                continue
            
            # Make prediction
            try:
                prediction = model.predict([features])[0]
                confidence = get_model_confidence(model, features)
                
                forecasts.append({
                    'date': forecast_date,
                    'predicted_value': max(0, prediction),  # Ensure non-negative
                    'confidence_score': confidence,
                    'meal_period': meal_period,
                    'dining_hall': dining_hall,
                    'food_item_id': food_item_id,
                    'model_type': model_type
                })
                
            except Exception as e:
                logger.error(f"Prediction failed for {forecast_date}: {e}")
                continue
        
        # Calculate confidence intervals
        forecasts = add_confidence_intervals(forecasts, model)
        
        # Save predictions to database
        save_predictions_to_database(forecasts, PredictionType.DEMAND_FORECAST)
        
        logger.info(f"Generated {len(forecasts)} demand forecasts")
        return forecasts
        
    except Exception as e:
        logger.error(f"Error generating demand forecast: {e}")
        return generate_fallback_forecast(days_ahead, meal_period, dining_hall)


def get_waste_prediction(
    days_ahead: int = 7,
    category: str = None,
    source: str = None,
    model_type: str = 'xgboost'
) -> List[Dict[str, Any]]:
    """
    Generate waste prediction for the specified period.
    
    Args:
        days_ahead: Number of days to predict
        category: Waste category to predict
        source: Waste source to predict
        model_type: ML model type to use
        
    Returns:
        list: Waste prediction data
    """
    try:
        # Load the appropriate model
        model = load_waste_model(model_type)
        if model is None:
            logger.warning(f"No trained waste model available for {model_type}, using fallback")
            return generate_fallback_waste_prediction(days_ahead, category, source)
        
        # Generate future dates
        prediction_dates = []
        base_date = date.today()
        
        for i in range(days_ahead):
            prediction_date = base_date + timedelta(days=i+1)
            prediction_dates.append(prediction_date)
        
        # Generate predictions
        predictions = []
        
        for prediction_date in prediction_dates:
            # Create feature vector
            features = extract_waste_features(prediction_date, category, source)
            
            if features is None:
                continue
            
            # Make prediction
            try:
                predicted_waste = model.predict([features])[0]
                confidence = get_model_confidence(model, features)
                
                predictions.append({
                    'date': prediction_date,
                    'predicted_value': max(0, predicted_waste),  # Ensure non-negative
                    'confidence_score': confidence,
                    'category': category,
                    'source': source,
                    'model_type': model_type
                })
                
            except Exception as e:
                logger.error(f"Waste prediction failed for {prediction_date}: {e}")
                continue
        
        # Calculate confidence intervals
        predictions = add_confidence_intervals(predictions, model)
        
        # Save predictions to database
        save_predictions_to_database(predictions, PredictionType.WASTE_PREDICTION)
        
        logger.info(f"Generated {len(predictions)} waste predictions")
        return predictions
        
    except Exception as e:
        logger.error(f"Error generating waste prediction: {e}")
        return generate_fallback_waste_prediction(days_ahead, category, source)


def train_demand_model(
    model_type: str = 'xgboost',
    days_back: int = 90,
    save_model: bool = True
) -> Dict[str, Any]:
    """
    Train a demand forecasting model.
    
    Args:
        model_type: Type of ML model to train
        days_back: Number of days of historical data to use
        save_model: Whether to save the trained model
        
    Returns:
        dict: Training results and model performance
    """
    try:
        logger.info(f"Training demand model: {model_type}")
        
        # Get historical data
        historical_data = get_historical_demand_data(days_back)
        
        if historical_data.empty:
            raise ValueError("No historical data available for training")
        
        # Prepare features and target
        X, y = prepare_demand_training_data(historical_data)
        
        if len(X) < 10:
            raise ValueError("Insufficient data for training (minimum 10 samples required)")
        
        # Split data for evaluation
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Initialize and train model
        model_class = MODEL_CLASSES.get(model_type)
        if not model_class:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model = model_class(random_state=42)
        
        # Train model
        model.fit(X_train, y_train)
        
        # Evaluate model
        y_pred = model.predict(X_test)
        
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'mape': calculate_mape(y_test, y_pred)
        }
        
        # Save model if requested
        model_info = None
        if save_model and metrics['r2'] > 0.5:  # Only save models with decent performance
            model_info = save_trained_model(model, model_type, 'demand', metrics)
        
        # Save model metadata to database
        save_model_metadata(model_type, 'demand', metrics, len(historical_data))
        
        logger.info(f"Model training completed. R²: {metrics['r2']:.3f}")
        
        return {
            'model_type': model_type,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'metrics': metrics,
            'model_info': model_info,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error training demand model: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_model_performance(
    model_type: str = None,
    prediction_type: str = None
) -> List[Dict[str, Any]]:
    """
    Get performance metrics for trained models.
    
    Args:
        model_type: Specific model type to query
        prediction_type: Specific prediction type to query
        
    Returns:
        list: Model performance data
    """
    try:
        db = get_session()
        
        # Query model metadata
        query = db.query(PredictionModel).filter(PredictionModel.is_active == True)
        
        if model_type:
            query = query.filter(PredictionModel.model_type == model_type)
        
        if prediction_type:
            query = query.filter(PredictionModel.prediction_type == prediction_type)
        
        models = query.order_by(PredictionModel.last_trained.desc()).all()
        
        performance_data = []
        
        for model in models:
            # Get latest metrics
            metrics = db.query(ModelMetrics).filter(
                ModelMetrics.model_id == model.id
            ).order_by(ModelMetrics.calculation_date.desc()).first()
            
            performance_data.append({
                'model_id': model.id,
                'name': model.name,
                'model_type': model.model_type,
                'prediction_type': model.prediction_type,
                'version': model.version,
                'last_trained': model.last_trained,
                'is_production': model.is_production,
                'training_score': model.training_score,
                'validation_score': model.validation_score,
                'test_score': model.test_score,
                'latest_metrics': {
                    'mae': metrics.metric_value if metrics and metrics.metric_type == 'mae' else None,
                    'rmse': metrics.metric_value if metrics and metrics.metric_type == 'rmse' else None,
                    'r2': metrics.metric_value if metrics and metrics.metric_type == 'r2' else None
                } if metrics else None
            })
        
        db.close()
        return performance_data
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        return []


def get_available_models(prediction_type: str = None) -> List[Dict[str, Any]]:
    """
    Get list of available trained models.
    
    Args:
        prediction_type: Filter by prediction type
        
    Returns:
        list: Available models
    """
    try:
        db = get_session()
        
        query = db.query(PredictionModel).filter(
            PredictionModel.is_active == True,
            PredictionModel.is_production == True
        )
        
        if prediction_type:
            query = query.filter(PredictionModel.prediction_type == prediction_type)
        
        models = query.all()
        
        model_list = []
        for model in models:
            model_list.append({
                'id': model.id,
                'name': model.name,
                'model_type': model.model_type,
                'prediction_type': model.prediction_type,
                'version': model.version,
                'last_trained': model.last_trained,
                'accuracy': model.test_score
            })
        
        db.close()
        return model_list
        
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        return []


# Helper functions

def get_historical_demand_data(days_back: int) -> pd.DataFrame:
    """Get historical demand data for training."""
    try:
        db = get_session()
        
        start_date = date.today() - timedelta(days=days_back)
        
        # Get waste records as proxy for demand
        records = db.query(WasteRecord).filter(
            WasteRecord.date >= start_date,
            WasteRecord.is_active == True
        ).all()
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'quantity_kg': float(record.quantity_kg),
                'category': record.category,
                'source': record.source,
                'meal_period': record.meal_period,
                'dining_hall': record.dining_hall,
                'day_of_week': record.date.weekday(),
                'day_of_month': record.date.day,
                'month': record.date.month,
                'is_weekend': record.date.weekday() >= 5
            })
        
        df = pd.DataFrame(data)
        db.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return pd.DataFrame()


def prepare_demand_training_data(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """Prepare training data for demand forecasting."""
    try:
        # Feature engineering
        features = []
        targets = []
        
        for _, row in df.iterrows():
            feature_vector = [
                row['day_of_week'],
                row['day_of_month'],
                row['month'],
                int(row['is_weekend']),
                # Add more features as needed
            ]
            
            # Encode categorical variables
            category_encoded = hash(row['category']) % 100
            source_encoded = hash(row['source']) % 100
            meal_encoded = hash(row['meal_period'] or '') % 100
            
            feature_vector.extend([category_encoded, source_encoded, meal_encoded])
            
            features.append(feature_vector)
            targets.append(row['quantity_kg'])
        
        return np.array(features), np.array(targets)
        
    except Exception as e:
        logger.error(f"Error preparing training data: {e}")
        return np.array([]), np.array([])


def extract_forecast_features(
    target_date: date,
    meal_period: str = None,
    dining_hall: str = None,
    food_item_id: int = None
) -> Optional[List[float]]:
    """Extract features for forecasting."""
    try:
        features = [
            target_date.weekday(),
            target_date.day,
            target_date.month,
            int(target_date.weekday() >= 5),  # is_weekend
        ]
        
        # Add encoded categorical features
        category_encoded = hash(meal_period or '') % 100
        hall_encoded = hash(dining_hall or '') % 100
        item_encoded = hash(str(food_item_id or 0)) % 100
        
        features.extend([category_encoded, hall_encoded, item_encoded])
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting forecast features: {e}")
        return None


def extract_waste_features(target_date: date, category: str = None, source: str = None) -> Optional[List[float]]:
    """Extract features for waste prediction."""
    try:
        features = [
            target_date.weekday(),
            target_date.day,
            target_date.month,
            int(target_date.weekday() >= 5),  # is_weekend
        ]
        
        # Add encoded categorical features
        category_encoded = hash(category or '') % 100
        source_encoded = hash(source or '') % 100
        
        features.extend([category_encoded, source_encoded])
        
        return features
        
    except Exception as e:
        logger.error(f"Error extracting waste features: {e}")
        return None


def load_demand_model(model_type: str):
    """Load trained demand model."""
    try:
        config = get_config()
        model_path = Path(config.ml_model_path) / f"demand_{model_type}.pkl"
        
        if model_path.exists():
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error loading demand model: {e}")
        return None


def load_waste_model(model_type: str):
    """Load trained waste model."""
    try:
        config = get_config()
        model_path = Path(config.ml_model_path) / f"waste_{model_type}.pkl"
        
        if model_path.exists():
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error loading waste model: {e}")
        return None


def save_trained_model(model, model_type: str, prediction_type: str, metrics: Dict) -> Dict[str, Any]:
    """Save trained model to disk."""
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        model_dir.mkdir(exist_ok=True)
        
        filename = f"{prediction_type}_{model_type}.pkl"
        model_path = model_dir / filename
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        return {
            'filename': filename,
            'path': str(model_path),
            'size_bytes': model_path.stat().st_size
        }
        
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return None


def get_model_confidence(model, features: List[float]) -> float:
    """Get confidence score for model prediction."""
    try:
        # For tree-based models, we can use prediction variance
        if hasattr(model, 'predict_proba'):
            # Not applicable for regression models
            return 0.8
        
        # Simple confidence based on model type and data
        if isinstance(model, (RandomForestRegressor, GradientBoostingRegressor)):
            return 0.85
        elif xgb is not None and isinstance(model, xgb.XGBRegressor):
            return 0.9
        elif lgb is not None and isinstance(model, lgb.LGBMRegressor):
            return 0.9
        else:
            return 0.75
            
    except Exception as e:
        logger.error(f"Error calculating model confidence: {e}")
        return 0.5


def add_confidence_intervals(predictions: List[Dict], model) -> List[Dict]:
    """Add confidence intervals to predictions."""
    try:
        for pred in predictions:
            # Simple confidence interval calculation
            confidence = pred['confidence_score']
            predicted_value = pred['predicted_value']
            
            # Calculate interval based on confidence
            margin = predicted_value * (1 - confidence) * 0.5
            
            pred['confidence_interval_lower'] = max(0, predicted_value - margin)
            pred['confidence_interval_upper'] = predicted_value + margin
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error adding confidence intervals: {e}")
        return predictions


def save_predictions_to_database(predictions: List[Dict], prediction_type: str):
    """Save predictions to database."""
    try:
        db = get_session()
        
        for pred in predictions:
            # Find or create model reference
            model = db.query(PredictionModel).filter(
                PredictionModel.model_type == pred['model_type'],
                PredictionModel.prediction_type == prediction_type,
                PredictionModel.is_production == True
            ).first()
            
            if not model:
                continue
            
            # Create prediction record
            prediction = Prediction(
                model_id=model.id,
                prediction_type=prediction_type,
                target_date=pred['date'],
                predicted_value=pred['predicted_value'],
                confidence_score=pred['confidence_score'],
                prediction_interval_lower=pred.get('confidence_interval_lower'),
                prediction_interval_upper=pred.get('confidence_interval_upper'),
                features_used=str(pred.get('features', {}))
            )
            
            db.add(prediction)
        
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error saving predictions to database: {e}")


def generate_fallback_forecast(days_ahead: int, meal_period: str, dining_hall: str) -> List[Dict[str, Any]]:
    """Generate fallback forecast using simple averaging."""
    try:
        # Get recent averages
        db = get_session()
        
        recent_data = db.query(WasteRecord).filter(
            WasteRecord.date >= date.today() - timedelta(days=7),
            WasteRecord.is_active == True
        )
        
        if meal_period:
            recent_data = recent_data.filter(WasteRecord.meal_period == meal_period)
        
        if dining_hall:
            recent_data = recent_data.filter(WasteRecord.dining_hall == dining_hall)
        
        records = recent_data.all()
        db.close()
        
        if not records:
            avg_quantity = 10.0  # Default fallback
        else:
            avg_quantity = sum(r.quantity_kg for r in records) / len(records)
        
        # Generate forecast
        forecasts = []
        base_date = date.today()
        
        for i in range(days_ahead):
            forecast_date = base_date + timedelta(days=i+1)
            
            # Add some variation
            variation = np.random.normal(0, 0.2)  # 20% variation
            predicted_value = max(0, avg_quantity * (1 + variation))
            
            forecasts.append({
                'date': forecast_date,
                'predicted_value': predicted_value,
                'confidence_score': 0.6,  # Lower confidence for fallback
                'meal_period': meal_period,
                'dining_hall': dining_hall,
                'model_type': 'fallback'
            })
        
        return forecasts
        
    except Exception as e:
        logger.error(f"Error generating fallback forecast: {e}")
        return []


def generate_fallback_waste_prediction(days_ahead: int, category: str, source: str) -> List[Dict[str, Any]]:
    """Generate fallback waste prediction."""
    try:
        # Similar to fallback forecast but for waste
        return generate_fallback_forecast(days_ahead, category, source)
        
    except Exception as e:
        logger.error(f"Error generating fallback waste prediction: {e}")
        return []


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error."""
    try:
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        mask = y_true != 0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    except:
        return float('inf')


def save_model_metadata(
    model_type: str,
    prediction_type: str,
    metrics: Dict,
    training_samples: int
):
    """Save model metadata to database."""
    try:
        db = get_session()
        
        # Create or update model record
        model = PredictionModel(
            name=f"{prediction_type}_{model_type}",
            description=f"ML model for {prediction_type} using {model_type}",
            model_type=model_type,
            prediction_type=prediction_type,
            version="1.0",
            training_score=metrics.get('r2', 0),
            validation_score=metrics.get('r2', 0),
            test_score=metrics.get('r2', 0),
            feature_count=10,  # Update based on actual features
            last_trained=datetime.utcnow(),
            is_active=True,
            is_production=True
        )
        
        db.add(model)
        db.commit()
        
        # Save individual metrics
        for metric_name, metric_value in metrics.items():
            if metric_name in ['mae', 'rmse', 'r2', 'mape']:
                metric_record = ModelMetrics(
                    model_id=model.id,
                    metric_type=metric_name,
                    metric_value=float(metric_value),
                    dataset_type='test'
                )
                db.add(metric_record)
        
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error saving model metadata: {e}")
