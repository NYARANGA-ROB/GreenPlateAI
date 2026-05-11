"""
Model training utilities for forecasting in GreenPlateAI.

This module provides functions for training, evaluating, and managing
machine learning models for food waste prediction.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
import pickle
import json
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database.connection import get_session
from models.prediction import PredictionModel, ModelMetrics
from utils.config import get_config
from .features import prepare_training_data, extract_features

logger = logging.getLogger(__name__)


def train_model(
    model_type: str,
    training_data: pd.DataFrame,
    target_column: str = 'quantity_kg',
    hyperparameters: Dict = None,
    validation_split: float = 0.2
) -> Dict[str, Any]:
    """
    Train a machine learning model.
    
    Args:
        model_type: Type of model to train
        training_data: Training data DataFrame
        target_column: Target variable column
        hyperparameters: Model hyperparameters
        validation_split: Validation split ratio
        
    Returns:
        dict: Training results
    """
    try:
        logger.info(f"Training {model_type} model")
        
        # Prepare data
        features_df = extract_features(training_data)
        
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Separate features and target
        X = features_df.drop(columns=[target_column, 'date'])
        y = features_df[target_column]
        
        # Remove non-numeric columns
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42
        )
        
        # Initialize model
        model = initialize_model(model_type, hyperparameters)
        
        # Train model
        start_time = datetime.utcnow()
        model.fit(X_train, y_train)
        training_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Evaluate model
        train_predictions = model.predict(X_train)
        val_predictions = model.predict(X_val)
        
        metrics = {
            'train_mae': mean_absolute_error(y_train, train_predictions),
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_predictions)),
            'train_r2': r2_score(y_train, train_predictions),
            'val_mae': mean_absolute_error(y_val, val_predictions),
            'val_rmse': np.sqrt(mean_squared_error(y_val, val_predictions)),
            'val_r2': r2_score(y_val, val_predictions)
        }
        
        # Feature importance
        feature_importance = get_feature_importance(model, X.columns.tolist())
        
        results = {
            'model': model,
            'model_type': model_type,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'feature_names': X.columns.tolist(),
            'metrics': metrics,
            'feature_importance': feature_importance,
            'training_time_seconds': training_time,
            'success': True
        }
        
        logger.info(f"Model training completed. Val R²: {metrics['val_r2']:.3f}")
        return results
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return {'success': False, 'error': str(e)}


def evaluate_model(
    model,
    test_data: pd.DataFrame,
    target_column: str = 'quantity_kg'
) -> Dict[str, Any]:
    """
    Evaluate a trained model on test data.
    
    Args:
        model: Trained model
        test_data: Test data DataFrame
        target_column: Target variable column
        
    Returns:
        dict: Evaluation results
    """
    try:
        # Prepare test data
        features_df = extract_features(test_data)
        
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Separate features and target
        X = features_df.drop(columns=[target_column, 'date'])
        y = features_df[target_column]
        
        # Remove non-numeric columns
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Make predictions
        predictions = model.predict(X)
        
        # Calculate metrics
        metrics = {
            'mae': mean_absolute_error(y, predictions),
            'rmse': np.sqrt(mean_squared_error(y, predictions)),
            'r2': r2_score(y, predictions),
            'mape': calculate_mape(y, predictions),
            'mean_prediction': np.mean(predictions),
            'std_prediction': np.std(predictions)
        }
        
        # Residual analysis
        residuals = y - predictions
        metrics.update({
            'mean_residual': np.mean(residuals),
            'std_residual': np.std(residuals),
            'residual_skewness': calculate_skewness(residuals)
        })
        
        return {
            'metrics': metrics,
            'predictions': predictions,
            'actual_values': y.values,
            'residuals': residuals,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error evaluating model: {e}")
        return {'success': False, 'error': str(e)}


def cross_validate_model(
    model_type: str,
    training_data: pd.DataFrame,
    target_column: str = 'quantity_kg',
    cv_folds: int = 5,
    hyperparameters: Dict = None
) -> Dict[str, Any]:
    """
    Perform cross-validation on a model.
    
    Args:
        model_type: Type of model to validate
        training_data: Training data
        target_column: Target variable column
        cv_folds: Number of cross-validation folds
        hyperparameters: Model hyperparameters
        
    Returns:
        dict: Cross-validation results
    """
    try:
        # Prepare data
        features_df = extract_features(training_data)
        
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Separate features and target
        X = features_df.drop(columns=[target_column, 'date'])
        y = features_df[target_column]
        
        # Remove non-numeric columns
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Initialize model
        model = initialize_model(model_type, hyperparameters)
        
        # Perform cross-validation
        scoring_metrics = ['neg_mean_absolute_error', 'neg_root_mean_squared_error', 'r2']
        cv_results = {}
        
        for metric in scoring_metrics:
            scores = cross_val_score(model, X, y, cv=cv_folds, scoring=metric)
            
            # Convert negative scores back to positive for MAE and RMSE
            if metric.startswith('neg_'):
                scores = -scores
            
            cv_results[metric] = {
                'scores': scores.tolist(),
                'mean': scores.mean(),
                'std': scores.std(),
                'min': scores.min(),
                'max': scores.max()
            }
        
        return {
            'cv_results': cv_results,
            'model_type': model_type,
            'cv_folds': cv_folds,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error in cross-validation: {e}")
        return {'success': False, 'error': str(e)}


def hyperparameter_tuning(
    model_type: str,
    training_data: pd.DataFrame,
    target_column: str = 'quantity_kg',
    param_grid: Dict = None,
    cv_folds: int = 3
) -> Dict[str, Any]:
    """
    Perform hyperparameter tuning using GridSearchCV.
    
    Args:
        model_type: Type of model to tune
        training_data: Training data
        target_column: Target variable column
        param_grid: Parameter grid for tuning
        cv_folds: Number of cross-validation folds
        
    Returns:
        dict: Tuning results
    """
    try:
        # Prepare data
        features_df = extract_features(training_data)
        
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        # Separate features and target
        X = features_df.drop(columns=[target_column, 'date'])
        y = features_df[target_column]
        
        # Remove non-numeric columns
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X = X[numeric_columns]
        
        # Get default parameter grid if not provided
        if param_grid is None:
            param_grid = get_default_param_grid(model_type)
        
        # Initialize model
        model = initialize_model(model_type)
        
        # Perform grid search
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=cv_folds,
            scoring='r2',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        # Get best model and results
        best_model = grid_search.best_estimator_
        best_params = grid_search.best_params_
        best_score = grid_search.best_score_
        
        # Evaluate best model
        evaluation = evaluate_model(best_model, training_data, target_column)
        
        return {
            'best_model': best_model,
            'best_params': best_params,
            'best_score': best_score,
            'cv_results': grid_search.cv_results_,
            'evaluation': evaluation,
            'model_type': model_type,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error in hyperparameter tuning: {e}")
        return {'success': False, 'error': str(e)}


def save_model(
    model,
    model_name: str,
    model_type: str,
    prediction_type: str,
    metrics: Dict,
    feature_names: List[str]
) -> Dict[str, Any]:
    """
    Save trained model to disk and database.
    
    Args:
        model: Trained model
        model_name: Name for the model
        model_type: Type of model
        prediction_type: Type of prediction
        metrics: Model performance metrics
        feature_names: List of feature names
        
    Returns:
        dict: Save results
    """
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        model_dir.mkdir(exist_ok=True)
        
        # Save model to disk
        model_filename = f"{prediction_type}_{model_type}_{model_name}.pkl"
        model_path = model_dir / model_filename
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        
        # Save model metadata
        metadata = {
            'model_name': model_name,
            'model_type': model_type,
            'prediction_type': prediction_type,
            'feature_names': feature_names,
            'metrics': metrics,
            'saved_at': datetime.utcnow().isoformat(),
            'file_size': model_path.stat().st_size
        }
        
        metadata_filename = f"{prediction_type}_{model_type}_{model_name}_metadata.json"
        metadata_path = model_dir / metadata_filename
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save to database
        save_model_to_database(model_name, model_type, prediction_type, metrics, len(feature_names))
        
        logger.info(f"Model saved: {model_filename}")
        
        return {
            'model_filename': model_filename,
            'metadata_filename': metadata_filename,
            'model_path': str(model_path),
            'metadata_path': str(metadata_path),
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Error saving model: {e}")
        return {'success': False, 'error': str(e)}


def load_model(
    model_name: str,
    model_type: str,
    prediction_type: str
) -> Any:
    """
    Load trained model from disk.
    
    Args:
        model_name: Name of the model
        model_type: Type of model
        prediction_type: Type of prediction
        
    Returns:
        Loaded model or None if not found
    """
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        
        model_filename = f"{prediction_type}_{model_type}_{model_name}.pkl"
        model_path = model_dir / model_filename
        
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_filename}")
            return None
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"Model loaded: {model_filename}")
        return model
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None


def list_saved_models(prediction_type: str = None) -> List[Dict[str, Any]]:
    """
    List all saved models.
    
    Args:
        prediction_type: Filter by prediction type
        
    Returns:
        list: List of model information
    """
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        
        models = []
        
        for model_file in model_dir.glob("*.pkl"):
            if model_file.name.endswith("_metadata.json"):
                continue
            
            # Parse filename
            parts = model_file.stem.split('_')
            if len(parts) >= 3:
                pred_type = parts[0]
                mod_type = parts[1]
                mod_name = '_'.join(parts[2:])
                
                if prediction_type and pred_type != prediction_type:
                    continue
                
                # Get metadata
                metadata_file = model_dir / f"{model_file.stem}_metadata.json"
                metadata = {}
                
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                
                models.append({
                    'name': mod_name,
                    'type': mod_type,
                    'prediction_type': pred_type,
                    'filename': model_file.name,
                    'file_size': model_file.stat().st_size,
                    'metadata': metadata
                })
        
        return models
        
    except Exception as e:
        logger.error(f"Error listing saved models: {e}")
        return []


def delete_model(
    model_name: str,
    model_type: str,
    prediction_type: str
) -> bool:
    """
    Delete saved model and metadata.
    
    Args:
        model_name: Name of the model
        model_type: Type of model
        prediction_type: Type of prediction
        
    Returns:
        bool: True if deletion successful
    """
    try:
        config = get_config()
        model_dir = Path(config.ml_model_path)
        
        # Delete model file
        model_filename = f"{prediction_type}_{model_type}_{model_name}.pkl"
        model_path = model_dir / model_filename
        
        if model_path.exists():
            model_path.unlink()
        
        # Delete metadata file
        metadata_filename = f"{prediction_type}_{model_type}_{model_name}_metadata.json"
        metadata_path = model_dir / metadata_filename
        
        if metadata_path.exists():
            metadata_path.unlink()
        
        logger.info(f"Model deleted: {model_filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting model: {e}")
        return False


# Helper functions

def initialize_model(model_type: str, hyperparameters: Dict = None):
    """Initialize model based on type."""
    try:
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import LinearRegression
        import xgboost as xgb
        import lightgbm as lgb
        
        hyperparams = hyperparameters or {}
        
        if model_type == 'linear_regression':
            return LinearRegression(**hyperparams)
        elif model_type == 'random_forest':
            return RandomForestRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                max_depth=hyperparams.get('max_depth', None),
                random_state=42,
                **{k: v for k, v in hyperparams.items() if k not in ['n_estimators', 'max_depth']}
            )
        elif model_type == 'gradient_boosting':
            return GradientBoostingRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                learning_rate=hyperparams.get('learning_rate', 0.1),
                max_depth=hyperparams.get('max_depth', 3),
                random_state=42,
                **{k: v for k, v in hyperparams.items() if k not in ['n_estimators', 'learning_rate', 'max_depth']}
            )
        elif model_type == 'xgboost':
            return xgb.XGBRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                learning_rate=hyperparams.get('learning_rate', 0.1),
                max_depth=hyperparams.get('max_depth', 6),
                random_state=42,
                **{k: v for k, v in hyperparams.items() if k not in ['n_estimators', 'learning_rate', 'max_depth']}
            )
        elif model_type == 'lightgbm':
            return lgb.LGBMRegressor(
                n_estimators=hyperparams.get('n_estimators', 100),
                learning_rate=hyperparams.get('learning_rate', 0.1),
                max_depth=hyperparams.get('max_depth', -1),
                random_state=42,
                **{k: v for k, v in hyperparams.items() if k not in ['n_estimators', 'learning_rate', 'max_depth']}
            )
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        return None


def get_feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    """Get feature importance from model."""
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            return {}
        
        importance_dict = {}
        for name, importance in zip(feature_names, importances):
            importance_dict[name] = float(importance)
        
        return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        return {}


def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error."""
    try:
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        mask = y_true != 0
        return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    except:
        return float('inf')


def calculate_skewness(data: np.ndarray) -> float:
    """Calculate skewness of data."""
    try:
        from scipy.stats import skew
        return float(skew(data))
    except:
        return 0.0


def get_default_param_grid(model_type: str) -> Dict[str, List]:
    """Get default parameter grid for hyperparameter tuning."""
    try:
        param_grids = {
            'random_forest': {
                'n_estimators': [50, 100, 200],
                'max_depth': [None, 10, 20, 30],
                'min_samples_split': [2, 5, 10]
            },
            'gradient_boosting': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7]
            },
            'xgboost': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 6, 9]
            },
            'lightgbm': {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [-1, 10, 20]
            }
        }
        
        return param_grids.get(model_type, {})
        
    except Exception as e:
        logger.error(f"Error getting default parameter grid: {e}")
        return {}


def save_model_to_database(
    model_name: str,
    model_type: str,
    prediction_type: str,
    metrics: Dict,
    feature_count: int
):
    """Save model metadata to database."""
    try:
        db = get_session()
        
        # Create model record
        model = PredictionModel(
            name=model_name,
            description=f"ML model for {prediction_type} using {model_type}",
            model_type=model_type,
            prediction_type=prediction_type,
            version="1.0",
            training_score=metrics.get('train_r2', 0),
            validation_score=metrics.get('val_r2', 0),
            test_score=metrics.get('val_r2', 0),
            feature_count=feature_count,
            last_trained=datetime.utcnow(),
            is_active=True,
            is_production=True
        )
        
        db.add(model)
        db.commit()
        
        # Save metrics
        for metric_name, metric_value in metrics.items():
            if metric_name in ['train_mae', 'train_rmse', 'train_r2', 'val_mae', 'val_rmse', 'val_r2']:
                metric_record = ModelMetrics(
                    model_id=model.id,
                    metric_type=metric_name.replace('train_', '').replace('val_', ''),
                    metric_value=float(metric_value),
                    dataset_type='train' if 'train_' in metric_name else 'validation'
                )
                db.add(metric_record)
        
        db.commit()
        db.close()
        
    except Exception as e:
        logger.error(f"Error saving model to database: {e}")
