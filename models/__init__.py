"""
SQLAlchemy models for GreenPlateAI.

This module contains all the data models used by the application,
including users, food items, waste records, and predictions.
"""

from .base import BaseModel
from .user import User, UserRole, Session
from .food_item import FoodItem, FoodCategory, Inventory, MenuItem
from .waste_record import WasteRecord, WasteCategory, WasteSource
from .prediction import Prediction, PredictionModel, ModelMetrics

__all__ = [
    # Base
    'BaseModel',
    
    # User models
    'User',
    'UserRole', 
    'Session',
    
    # Food item models
    'FoodItem',
    'FoodCategory',
    'Inventory',
    'MenuItem',
    
    # Waste record models
    'WasteRecord',
    'WasteCategory',
    'WasteSource',
    
    # Prediction models
    'Prediction',
    'PredictionModel',
    'ModelMetrics'
]
