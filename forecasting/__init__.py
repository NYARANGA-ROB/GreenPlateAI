"""
Forecasting module for GreenPlateAI.

This module provides machine learning models and utilities for
predicting food demand, waste patterns, and consumption trends.
"""

from .models import (
    get_demand_forecast, get_waste_prediction, train_demand_model,
    get_model_performance, get_available_models
)
from .features import (
    extract_features, prepare_training_data, create_feature_matrix,
    feature_engineering_pipeline
)
from .training import (
    train_model, evaluate_model, save_model, load_model,
    cross_validate_model, hyperparameter_tuning
)
from .prediction import (
    make_prediction, batch_predict, get_prediction_confidence,
    update_actual_values, calculate_prediction_accuracy
)

__all__ = [
    # Models
    'get_demand_forecast',
    'get_waste_prediction', 
    'train_demand_model',
    'get_model_performance',
    'get_available_models',
    
    # Features
    'extract_features',
    'prepare_training_data',
    'create_feature_matrix',
    'feature_engineering_pipeline',
    
    # Training
    'train_model',
    'evaluate_model',
    'save_model',
    'load_model',
    'cross_validate_model',
    'hyperparameter_tuning',
    
    # Prediction
    'make_prediction',
    'batch_predict',
    'get_prediction_confidence',
    'update_actual_values',
    'calculate_prediction_accuracy'
]
