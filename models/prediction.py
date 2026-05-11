"""
Machine learning prediction models.

This module contains models for storing and managing ML predictions,
model metadata, and performance metrics.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, ForeignKey, DateTime, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class PredictionType(str, Enum):
    """Types of predictions available."""
    DEMAND_FORECAST = "demand_forecast"
    WASTE_PREDICTION = "waste_prediction"
    INVENTORY_OPTIMIZATION = "inventory_optimization"
    CONSUMPTION_PATTERN = "consumption_pattern"
    SEASONAL_TREND = "seasonal_trend"


class PredictionModel(BaseModel):
    """ML model metadata and configuration."""
    
    __tablename__ = "prediction_models"
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    model_type = Column(String(50), nullable=False)  # linear, xgboost, random_forest, etc.
    prediction_type = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    file_path = Column(String(500))
    model_size_mb = Column(Float)
    training_data_start = Column(Date)
    training_data_end = Column(Date)
    feature_count = Column(Integer)
    target_variable = Column(String(100))
    hyperparameters = Column(Text)  # JSON object
    feature_importance = Column(Text)  # JSON object
    training_score = Column(Float)
    validation_score = Column(Float)
    test_score = Column(Float)
    cross_validation_score = Column(Float)
    training_time_seconds = Column(Float)
    last_trained = Column(DateTime)
    is_active = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)
    created_by = Column(String(50))
    accuracy_threshold = Column(Float, default=0.8)
    min_confidence_score = Column(Float, default=0.7)
    
    @property
    def is_outdated(self, days_threshold: int = 30) -> bool:
        """Check if model needs retraining."""
        if not self.last_trained:
            return True
        days_since_training = (datetime.utcnow() - self.last_trained).days
        return days_since_training > days_threshold
    
    @property
    def model_health(self) -> str:
        """Assess model health based on performance metrics."""
        if not self.test_score:
            return "unknown"
        
        if self.test_score >= 0.9:
            return "excellent"
        elif self.test_score >= 0.8:
            return "good"
        elif self.test_score >= 0.7:
            return "fair"
        else:
            return "poor"


class ModelMetrics(BaseModel):
    """Performance metrics for ML models."""
    
    __tablename__ = "model_metrics"
    
    model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)  # accuracy, precision, recall, f1, mae, rmse, etc.
    metric_value = Column(Float, nullable=False)
    dataset_type = Column(String(20), nullable=False)  # training, validation, test
    calculation_date = Column(DateTime, default=datetime.utcnow)
    confidence_interval_lower = Column(Float)
    confidence_interval_upper = Column(Float)
    sample_size = Column(Integer)
    additional_info = Column(Text)  # JSON object for additional metric details
    
    # Relationships
    model = relationship("PredictionModel")
    
    @property
    def metric_display_name(self) -> str:
        """Get display name for metric."""
        display_names = {
            "accuracy": "Accuracy",
            "precision": "Precision",
            "recall": "Recall",
            "f1": "F1 Score",
            "mae": "Mean Absolute Error",
            "rmse": "Root Mean Square Error",
            "r2": "R² Score",
            "mape": "Mean Absolute Percentage Error"
        }
        return display_names.get(self.metric_type, self.metric_type.title())


class Prediction(BaseModel):
    """Individual prediction records."""
    
    __tablename__ = "predictions"
    
    model_id = Column(Integer, ForeignKey("prediction_models.id"), nullable=False)
    prediction_type = Column(String(50), nullable=False)
    target_date = Column(Date, nullable=False, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    dining_hall = Column(String(100))
    meal_period = Column(String(20))
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float)
    prediction_interval_lower = Column(Float)
    prediction_interval_upper = Column(Float)
    actual_value = Column(Float)
    accuracy_percentage = Column(Float)
    features_used = Column(Text)  # JSON object
    prediction_metadata = Column(Text)  # JSON object
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(50))
    verified_at = Column(DateTime)
    created_by = Column(String(50))
    
    # Relationships
    model = relationship("PredictionModel", back_populates="predictions")
    food_item = relationship("FoodItem")
    
    @property
    def prediction_error(self) -> Optional[float]:
        """Calculate prediction error if actual value exists."""
        if self.actual_value is None:
            return None
        return abs(self.predicted_value - self.actual_value)
    
    @property
    def percentage_error(self) -> Optional[float]:
        """Calculate percentage error if actual value exists."""
        if self.actual_value is None or self.actual_value == 0:
            return None
        return (self.prediction_error / self.actual_value) * 100
    
    @property
    def is_accurate(self, tolerance_percent: float = 20.0) -> bool:
        """Check if prediction is within tolerance."""
        if self.percentage_error is None:
            return False
        return self.percentage_error <= tolerance_percent
    
    def update_actual_value(self, actual_value: float, verified_by: str = None) -> None:
        """Update actual value and calculate accuracy."""
        self.actual_value = actual_value
        if self.predicted_value != 0:
            self.accuracy_percentage = (1 - abs(self.predicted_value - actual_value) / self.predicted_value) * 100
        self.is_verified = True
        self.verified_by = verified_by
        self.verified_at = datetime.utcnow()


class ForecastingJob(BaseModel):
    """Background job tracking for model training and prediction."""
    
    __tablename__ = "forecasting_jobs"
    
    job_name = Column(String(200), nullable=False)
    job_type = Column(String(50), nullable=False)  # training, prediction, evaluation
    model_id = Column(Integer, ForeignKey("prediction_models.id"))
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    priority = Column(String(10), default="medium")  # low, medium, high
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    parameters = Column(Text)  # JSON object
    progress_percentage = Column(Float, default=0.0)
    current_step = Column(String(200))
    error_message = Column(Text)
    result_summary = Column(Text)  # JSON object
    created_by = Column(String(50))
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == "running"
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed."""
        return self.status == "completed"
    
    @property
    def is_failed(self) -> bool:
        """Check if job failed."""
        return self.status == "failed"
    
    def start_job(self) -> None:
        """Mark job as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()
        self.progress_percentage = 0.0
    
    def complete_job(self, result_summary: str = None) -> None:
        """Mark job as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.progress_percentage = 100.0
        if result_summary:
            self.result_summary = result_summary
    
    def fail_job(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.error_message = error_message
    
    def update_progress(self, progress: float, step: str = None) -> None:
        """Update job progress."""
        self.progress_percentage = max(0.0, min(100.0, progress))
        if step:
            self.current_step = step


# Add relationship to PredictionModel
PredictionModel.predictions = relationship("Prediction", back_populates="model")
