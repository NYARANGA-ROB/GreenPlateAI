"""
Prediction utilities for forecasting in GreenPlateAI.

This module provides functions for making predictions, managing
prediction results, and calculating prediction accuracy.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
from pathlib import Path
import pickle

from database.connection import get_session
from models.prediction import Prediction, PredictionModel, PredictionType
from models.waste_record import WasteRecord
from utils.config import get_config
from .features import create_feature_matrix

logger = logging.getLogger(__name__)


def make_prediction(
    model_type: str,
    prediction_type: str,
    target_date: date,
    features: Dict = None,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Make a single prediction.
    
    Args:
        model_type: Type of model to use
        prediction_type: Type of prediction
        target_date: Date for prediction
        features: Additional features for prediction
        confidence_threshold: Minimum confidence threshold
        
    Returns:
        dict: Prediction result
    """
    try:
        # Load model
        model = load_prediction_model(model_type, prediction_type)
        if model is None:
            raise ValueError(f"No trained model available for {prediction_type}_{model_type}")
        
        # Create feature matrix
        feature_matrix = create_feature_matrix(
            dates=[target_date],
            meal_period=features.get('meal_period'),
            dining_hall=features.get('dining_hall'),
            category=features.get('category')
        )
        
        if feature_matrix.empty:
            raise ValueError("Failed to create feature matrix")
        
        # Prepare features for model
        X = prepare_features_for_prediction(feature_matrix, model)
        
        # Make prediction
        prediction_value = model.predict(X)[0]
        confidence = calculate_prediction_confidence(model, X, prediction_value)
        
        # Check confidence threshold
        if confidence < confidence_threshold:
            logger.warning(f"Low confidence prediction: {confidence:.3f}")
        
        # Calculate prediction interval
        interval_lower, interval_upper = calculate_prediction_interval(
            model, X, prediction_value, confidence
        )
        
        result = {
            'date': target_date,
            'predicted_value': max(0, prediction_value),  # Ensure non-negative
            'confidence_score': confidence,
            'prediction_interval_lower': max(0, interval_lower),
            'prediction_interval_upper': interval_upper,
            'model_type': model_type,
            'prediction_type': prediction_type,
            'features_used': features or {},
            'meets_threshold': confidence >= confidence_threshold
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        return {'success': False, 'error': str(e)}


def batch_predict(
    model_type: str,
    prediction_type: str,
    dates: List[date],
    features: Dict = None
) -> List[Dict[str, Any]]:
    """
    Make batch predictions for multiple dates.
    
    Args:
        model_type: Type of model to use
        prediction_type: Type of prediction
        dates: List of dates for predictions
        features: Additional features for predictions
        
    Returns:
        list: List of prediction results
    """
    try:
        logger.info(f"Making batch predictions for {len(dates)} dates")
        
        # Load model
        model = load_prediction_model(model_type, prediction_type)
        if model is None:
            raise ValueError(f"No trained model available for {prediction_type}_{model_type}")
        
        # Create feature matrix for all dates
        feature_matrix = create_feature_matrix(
            dates=dates,
            meal_period=features.get('meal_period'),
            dining_hall=features.get('dining_hall'),
            category=features.get('category')
        )
        
        if feature_matrix.empty:
            raise ValueError("Failed to create feature matrix")
        
        # Prepare features for model
        X = prepare_features_for_prediction(feature_matrix, model)
        
        # Make batch predictions
        predictions = model.predict(X)
        
        # Calculate confidence scores
        confidences = []
        for i in range(len(X)):
            confidence = calculate_prediction_confidence(model, X[i:i+1], predictions[i])
            confidences.append(confidence)
        
        # Create results
        results = []
        for i, target_date in enumerate(dates):
            prediction_value = predictions[i]
            confidence = confidences[i]
            
            # Calculate prediction interval
            interval_lower, interval_upper = calculate_prediction_interval(
                model, X[i:i+1], prediction_value, confidence
            )
            
            result = {
                'date': target_date,
                'predicted_value': max(0, prediction_value),
                'confidence_score': confidence,
                'prediction_interval_lower': max(0, interval_lower),
                'prediction_interval_upper': interval_upper,
                'model_type': model_type,
                'prediction_type': prediction_type,
                'features_used': features or {}
            }
            
            results.append(result)
        
        # Save predictions to database
        save_batch_predictions(results)
        
        logger.info(f"Batch prediction completed: {len(results)} predictions")
        return results
        
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}")
        return []


def get_prediction_confidence(
    model,
    features: np.ndarray,
    prediction: float
) -> float:
    """
    Calculate confidence score for a prediction.
    
    Args:
        model: Trained model
        features: Feature vector
        prediction: Predicted value
        
    Returns:
        float: Confidence score (0-1)
    """
    try:
        # For ensemble models, use prediction variance
        if hasattr(model, 'estimators_'):
            # Get predictions from all estimators
            estimator_predictions = []
            for estimator in model.estimators_:
                pred = estimator.predict(features)[0]
                estimator_predictions.append(pred)
            
            # Calculate variance as confidence measure
            variance = np.var(estimator_predictions)
            max_variance = np.var([prediction * 0.5, prediction * 1.5])  # Max expected variance
            
            confidence = 1.0 - (variance / max_variance)
            return max(0.0, min(1.0, confidence))
        
        # For other models, use model-specific confidence
        elif hasattr(model, 'predict_proba'):
            # Not applicable for regression
            return 0.8
        
        # Default confidence based on model type
        elif hasattr(model, 'feature_importances_'):
            return 0.85
        else:
            return 0.75
        
    except Exception as e:
        logger.error(f"Error calculating prediction confidence: {e}")
        return 0.5


def calculate_prediction_interval(
    model,
    features: np.ndarray,
    prediction: float,
    confidence: float,
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate prediction interval for a prediction.
    
    Args:
        model: Trained model
        features: Feature vector
        prediction: Predicted value
        confidence: Confidence score
        alpha: Significance level for interval
        
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    try:
        # Simple interval calculation based on confidence
        # Higher confidence = narrower interval
        margin_factor = (1.0 - confidence) * 0.5  # Scale factor for margin
        
        # Base margin as percentage of prediction
        base_margin = prediction * 0.2  # 20% base margin
        
        # Adjust margin based on confidence
        margin = base_margin * (1 + margin_factor)
        
        # Calculate bounds
        lower_bound = max(0, prediction - margin)
        upper_bound = prediction + margin
        
        return lower_bound, upper_bound
        
    except Exception as e:
        logger.error(f"Error calculating prediction interval: {e}")
        return max(0, prediction * 0.8), prediction * 1.2


def update_actual_values(
    prediction_id: int,
    actual_value: float,
    verified_by: str = None
) -> bool:
    """
    Update actual value for a prediction.
    
    Args:
        prediction_id: Prediction ID
        actual_value: Actual observed value
        verified_by: User who verified the value
        
    Returns:
        bool: True if update successful
    """
    try:
        db = get_session()
        
        prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
        if not prediction:
            return False
        
        # Update actual value and calculate accuracy
        prediction.actual_value = actual_value
        prediction.is_verified = True
        prediction.verified_by = verified_by
        prediction.verified_at = datetime.utcnow()
        
        # Calculate accuracy percentage
        if prediction.predicted_value != 0:
            accuracy = (1 - abs(prediction.predicted_value - actual_value) / abs(prediction.predicted_value)) * 100
            prediction.accuracy_percentage = max(0, min(100, accuracy))
        
        db.commit()
        db.close()
        
        logger.info(f"Updated actual value for prediction {prediction_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating actual value: {e}")
        return False


def calculate_prediction_accuracy(
    model_type: str = None,
    prediction_type: str = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Calculate prediction accuracy metrics.
    
    Args:
        model_type: Filter by model type
        prediction_type: Filter by prediction type
        days_back: Number of days to analyze
        
    Returns:
        dict: Accuracy metrics
    """
    try:
        db = get_session()
        
        # Get predictions with actual values
        start_date = date.today() - timedelta(days=days_back)
        
        query = db.query(Prediction).filter(
            Prediction.target_date >= start_date,
            Prediction.actual_value.isnot(None),
            Prediction.is_verified == True
        )
        
        if model_type:
            query = query.join(PredictionModel).filter(PredictionModel.model_type == model_type)
        
        if prediction_type:
            query = query.filter(Prediction.prediction_type == prediction_type)
        
        predictions = query.all()
        
        if not predictions:
            return {
                'total_predictions': 0,
                'accuracy_metrics': {},
                'message': 'No verified predictions found'
            }
        
        # Calculate accuracy metrics
        predicted_values = [p.predicted_value for p in predictions]
        actual_values = [p.actual_value for p in predictions]
        accuracies = [p.accuracy_percentage for p in predictions if p.accuracy_percentage is not None]
        
        metrics = {
            'total_predictions': len(predictions),
            'mean_accuracy': np.mean(accuracies) if accuracies else 0,
            'median_accuracy': np.median(accuracies) if accuracies else 0,
            'min_accuracy': np.min(accuracies) if accuracies else 0,
            'max_accuracy': np.max(accuracies) if accuracies else 0,
            'mae': mean_absolute_error(actual_values, predicted_values),
            'rmse': np.sqrt(mean_squared_error(actual_values, predicted_values)),
            'r2': r2_score(actual_values, predicted_values),
            'mape': calculate_mape(actual_values, predicted_values)
        }
        
        # Accuracy distribution
        accuracy_ranges = {
            'excellent (>90%)': len([a for a in accuracies if a > 90]),
            'good (70-90%)': len([a for a in accuracies if 70 <= a <= 90]),
            'fair (50-70%)': len([a for a in accuracies if 50 <= a < 70]),
            'poor (<50%)': len([a for a in accuracies if a < 50])
        }
        
        metrics['accuracy_distribution'] = accuracy_ranges
        
        db.close()
        
        logger.info(f"Calculated accuracy for {len(predictions)} predictions")
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating prediction accuracy: {e}")
        return {'error': str(e)}


def get_prediction_history(
    prediction_type: str = None,
    days_back: int = 30,
    include_actual: bool = True
) -> List[Dict[str, Any]]:
    """
    Get prediction history.
    
    Args:
        prediction_type: Filter by prediction type
        days_back: Number of days to look back
        include_actual: Whether to include actual values
        
    Returns:
        list: Prediction history
    """
    try:
        db = get_session()
        
        start_date = date.today() - timedelta(days=days_back)
        
        query = db.query(Prediction).filter(
            Prediction.target_date >= start_date
        )
        
        if prediction_type:
            query = query.filter(Prediction.prediction_type == prediction_type)
        
        predictions = query.order_by(Prediction.target_date.desc()).all()
        
        history = []
        for pred in predictions:
            record = {
                'id': pred.id,
                'date': pred.target_date,
                'predicted_value': pred.predicted_value,
                'confidence_score': pred.confidence_score,
                'prediction_type': pred.prediction_type,
                'model_type': pred.model.model_type if pred.model else 'unknown',
                'created_at': pred.created_at
            }
            
            if include_actual:
                record.update({
                    'actual_value': pred.actual_value,
                    'accuracy_percentage': pred.accuracy_percentage,
                    'is_verified': pred.is_verified,
                    'verified_at': pred.verified_at
                })
            
            history.append(record)
        
        db.close()
        return history
        
    except Exception as e:
        logger.error(f"Error getting prediction history: {e}")
        return []


def compare_predictions(
    model_types: List[str],
    prediction_type: str,
    target_date: date
) -> Dict[str, Any]:
    """
    Compare predictions from different models.
    
    Args:
        model_types: List of model types to compare
        prediction_type: Type of prediction
        target_date: Target date for comparison
        
    Returns:
        dict: Comparison results
    """
    try:
        results = {}
        
        for model_type in model_types:
            prediction = make_prediction(model_type, prediction_type, target_date)
            
            if prediction.get('success', True):
                results[model_type] = {
                    'predicted_value': prediction.get('predicted_value'),
                    'confidence': prediction.get('confidence_score'),
                    'interval_lower': prediction.get('prediction_interval_lower'),
                    'interval_upper': prediction.get('prediction_interval_upper')
                }
            else:
                results[model_type] = {'error': prediction.get('error', 'Unknown error')}
        
        # Calculate consensus prediction
        valid_predictions = {k: v for k, v in results.items() if 'error' not in v}
        
        if valid_predictions:
            values = [v['predicted_value'] for v in valid_predictions.values()]
            confidences = [v['confidence'] for v in valid_predictions.values()]
            
            # Weighted average based on confidence
            weighted_sum = sum(v * c for v, c in zip(values, confidences))
            total_confidence = sum(confidences)
            
            consensus = weighted_sum / total_confidence if total_confidence > 0 else np.mean(values)
            
            results['consensus'] = {
                'predicted_value': consensus,
                'confidence': np.mean(confidences),
                'models_used': list(valid_predictions.keys())
            }
        
        return results
        
    except Exception as e:
        logger.error(f"Error comparing predictions: {e}")
        return {'error': str(e)}


# Helper functions

def load_prediction_model(model_type: str, prediction_type: str):
    """Load trained prediction model."""
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        
        # Look for the latest model file
        pattern = f"{prediction_type}_{model_type}_*.pkl"
        model_files = list(model_dir.glob(pattern))
        
        if not model_files:
            return None
        
        # Get the most recent model
        latest_model = max(model_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_model, 'rb') as f:
            model = pickle.load(f)
        
        return model
        
    except Exception as e:
        logger.error(f"Error loading prediction model: {e}")
        return None


def prepare_features_for_prediction(feature_matrix: pd.DataFrame, model) -> np.ndarray:
    """Prepare features for model prediction."""
    try:
        # Remove non-numeric columns
        numeric_columns = feature_matrix.select_dtypes(include=[np.number]).columns
        
        # Ensure we have the same features as during training
        if hasattr(model, 'feature_names_in_'):
            # Get features the model was trained on
            model_features = model.feature_names_in_
            
            # Align features
            available_features = [col for col in model_features if col in numeric_columns]
            X = feature_matrix[available_features]
            
            # Add missing features with zeros
            for feature in model_features:
                if feature not in X.columns:
                    X[feature] = 0
            
            X = X[model_features]  # Ensure correct order
        else:
            # Fallback to all numeric features
            X = feature_matrix[numeric_columns]
        
        return X.values
        
    except Exception as e:
        logger.error(f"Error preparing features for prediction: {e}")
        return np.array([])


def save_batch_predictions(predictions: List[Dict[str, Any]]):
    """Save batch predictions to database."""
    try:
        db = get_session()
        
        for pred in predictions:
            # Find model reference
            model = db.query(PredictionModel).filter(
                PredictionModel.model_type == pred['model_type'],
                PredictionModel.prediction_type == pred['prediction_type'],
                PredictionModel.is_production == True
            ).first()
            
            if not model:
                continue
            
            # Create prediction record
            prediction = Prediction(
                model_id=model.id,
                prediction_type=pred['prediction_type'],
                target_date=pred['date'],
                predicted_value=pred['predicted_value'],
                confidence_score=pred['confidence_score'],
                prediction_interval_lower=pred.get('prediction_interval_lower'),
                prediction_interval_upper=pred.get('prediction_interval_upper'),
                features_used=str(pred.get('features_used', {}))
            )
            
            db.add(prediction)
        
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error saving batch predictions: {e}")


def mean_absolute_error(y_true, y_pred):
    """Calculate Mean Absolute Error."""
    return np.mean(np.abs(np.array(y_true) - np.array(y_pred)))


def mean_squared_error(y_true, y_pred):
    """Calculate Mean Squared Error."""
    return np.mean((np.array(y_true) - np.array(y_pred)) ** 2)


def r2_score(y_true, y_pred):
    """Calculate R² Score."""
    ss_res = np.sum((np.array(y_true) - np.array(y_pred)) ** 2)
    ss_tot = np.sum((np.array(y_true) - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot) if ss_tot != 0 else 0


def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error."""
    try:
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        mask = y_true != 0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    except:
        return float('inf')
