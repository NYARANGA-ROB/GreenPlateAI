"""
SQLAlchemy database models for GreenPlateAI.

This module contains all database models with proper relationships,
CRUD helper methods, and production-ready architecture.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, 
    Text, ForeignKey, Enum, JSON, Numeric, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session, validates
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import DATETIME, FLOAT
import enum
import json

Base = declarative_base()


# Enums for type safety
class UserRole(str, enum.Enum):
    """User roles in the system."""
    ADMIN = "admin"
    KITCHEN_STAFF = "kitchen_staff"
    STUDENT = "student"
    MANAGER = "manager"


class MealType(str, enum.Enum):
    """Meal period types."""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class WasteCategory(str, enum.Enum):
    """Food waste categories."""
    PREPARATION = "preparation"
    PLATE_WASTE = "plate_waste"
    SPOILAGE = "spoilage"
    EXPIRED = "expired"
    OVERPRODUCTION = "overproduction"
    OTHER = "other"


class AlertType(str, enum.Enum):
    """Alert types."""
    HIGH_WASTE = "high_waste"
    LOW_INVENTORY = "low_inventory"
    EXPIRATION_WARNING = "expiration_warning"
    SYSTEM_ERROR = "system_error"
    MAINTENANCE = "maintenance"
    PREDICTION_ALERT = "prediction_alert"


class FeedbackType(str, enum.Enum):
    """Feedback types."""
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    COMPLIMENT = "compliment"
    QUESTION = "question"
    REPORT = "report"


class PredictionStatus(str, enum.Enum):
    """Prediction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class AlertStatus(str, enum.Enum):
    """Alert statuses."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


# Base Model with Common Fields and Methods
class BaseModel(Base):
    """Base model with common fields and CRUD methods."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Common CRUD methods
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude_fields = exclude_fields or []
        
        result = {}
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                
                # Handle datetime serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif isinstance(value, date):
                    value = value.isoformat()
                elif isinstance(value, enum.Enum):
                    value = value.value
                elif isinstance(value, (dict, list)):
                    value = json.dumps(value) if isinstance(value, dict) else value
                
                result[column.name] = value
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], session: Session = None) -> 'BaseModel':
        """Create model instance from dictionary."""
        instance = cls()
        
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        return instance
    
    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key) and key not in ['id', 'created_at']:
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the record."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore soft deleted record."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    @classmethod
    def create(cls, session: Session, **kwargs) -> 'BaseModel':
        """Create new record."""
        instance = cls(**kwargs)
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance
    
    @classmethod
    def get_by_id(cls, session: Session, record_id: int) -> Optional['BaseModel']:
        """Get record by ID."""
        return session.query(cls).filter(
            cls.id == record_id,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_all(cls, session: Session, active_only: bool = True) -> List['BaseModel']:
        """Get all records."""
        query = session.query(cls)
        
        if active_only:
            query = query.filter(cls.is_active == True)
        
        return query.all()
    
    @classmethod
    def get_by_field(cls, session: Session, field_name: str, value: Any) -> Optional['BaseModel']:
        """Get record by field value."""
        if not hasattr(cls, field_name):
            raise AttributeError(f"Model {cls.__name__} has no field {field_name}")
        
        field = getattr(cls, field_name)
        return session.query(cls).filter(
            field == value,
            cls.is_active == True
        ).first()
    
    def update(self, session: Session, **kwargs) -> 'BaseModel':
        """Update record."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(self)
        return self
    
    def delete(self, session: Session, soft: bool = True) -> None:
        """Delete record."""
        if soft:
            self.soft_delete()
        else:
            session.delete(self)
        
        session.commit()


# User Model
class User(BaseModel):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    
    # Profile fields
    full_name = Column(String(255))
    phone = Column(String(20))
    department = Column(String(100))
    student_id = Column(String(50))
    employee_id = Column(String(50))
    
    # Status fields
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    
    # Preferences
    preferences = Column(JSON)  # User preferences as JSON
    
    # Relationships
    meal_logs = relationship("MealLog", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        import re
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError("Invalid email format")
        return email
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def is_kitchen_staff(self) -> bool:
        """Check if user is kitchen staff."""
        return self.role == UserRole.KITCHEN_STAFF
    
    @property
    def is_student(self) -> bool:
        """Check if user is student."""
        return self.role == UserRole.STUDENT
    
    def lock_account(self, hours: int = 24) -> None:
        """Lock user account for specified hours."""
        self.locked_until = datetime.utcnow() + timedelta(hours=hours)
        self.failed_login_attempts = 0
    
    def unlock_account(self) -> None:
        """Unlock user account."""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        self.login_count = (self.login_count or 0) + 1
    
    def get_permissions(self) -> List[str]:
        """Get user permissions based on role."""
        permissions = {
            UserRole.ADMIN: [
                "manage_users", "manage_system", "view_all_reports", 
                "manage_inventory", "manage_kitchen", "view_dashboard",
                "manage_predictions", "manage_alerts"
            ],
            UserRole.MANAGER: [
                "manage_inventory", "manage_kitchen", "view_reports", 
                "view_dashboard", "manage_predictions"
            ],
            UserRole.KITCHEN_STAFF: [
                "manage_inventory", "view_reports", "view_dashboard"
            ],
            UserRole.STUDENT: [
                "view_dashboard", "create_feedback"
            ]
        }
        return permissions.get(self.role, [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.get_permissions()


# MealLog Model
class MealLog(BaseModel):
    """Meal consumption tracking model."""
    
    __tablename__ = "meal_logs"
    
    # User and meal information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_type = Column(Enum(MealType), nullable=False)
    dining_hall = Column(String(100), nullable=False)
    
    # Meal details
    meal_items = Column(JSON)  # List of meal items
    calories = Column(Integer)
    protein = Column(Float)  # grams
    carbs = Column(Float)  # grams
    fat = Column(Float)  # grams
    fiber = Column(Float)  # grams
    
    # Satisfaction and feedback
    satisfaction_rating = Column(Integer)  # 1-5 scale
    portion_size_rating = Column(Integer)  # 1-5 scale
    taste_rating = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    
    # Timing
    meal_date = Column(Date, default=date.today, nullable=False)
    meal_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="meal_logs")
    
    @validates('satisfaction_rating', 'portion_size_rating', 'taste_rating')
    def validate_ratings(self, key, rating):
        """Validate rating values."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError(f"{key} must be between 1 and 5")
        return rating
    
    @validates('calories')
    def validate_calories(self, key, calories):
        """Validate calories."""
        if calories is not None and calories < 0:
            raise ValueError("Calories cannot be negative")
        return calories
    
    @validates('protein', 'carbs', 'fat', 'fiber')
    def validate_macros(self, key, value):
        """Validate macronutrient values."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @property
    def total_macros(self) -> float:
        """Calculate total macronutrients."""
        return (self.protein or 0) + (self.carbs or 0) + (self.fat or 0)
    
    @classmethod
    def get_by_user_and_date(cls, session: Session, user_id: int, meal_date: date) -> List['MealLog']:
        """Get meal logs for user on specific date."""
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.meal_date == meal_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_by_dining_hall(cls, session: Session, dining_hall: str, start_date: date, end_date: date) -> List['MealLog']:
        """Get meal logs for dining hall in date range."""
        return session.query(cls).filter(
            cls.dining_hall == dining_hall,
            cls.meal_date >= start_date,
            cls.meal_date <= end_date,
            cls.is_active == True
        ).all()


# FoodWasteLog Model
class FoodWasteLog(BaseModel):
    """Food waste tracking model."""
    
    __tablename__ = "food_waste_logs"
    
    # Waste identification
    food_item = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    waste_category = Column(Enum(WasteCategory), nullable=False)
    
    # Quantities
    quantity_kg = Column(Float, nullable=False)
    quantity_servings = Column(Integer)
    estimated_cost = Column(Float)  # monetary value
    
    # Location and source
    dining_hall = Column(String(100), nullable=False)
    meal_period = Column(Enum(MealType))
    source_station = Column(String(100))  # Where waste originated
    
    # Timing
    waste_date = Column(Date, default=date.today, nullable=False)
    waste_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Additional data
    reason = Column(Text)  # Reason for waste
    temperature = Column(Float)  # Temperature at time of waste
    storage_conditions = Column(String(255))
    preparation_method = Column(String(100))
    
    # Environmental impact
    co2_equivalent_kg = Column(Float)  # CO2 equivalent in kg
    water_footprint_liters = Column(Float)
    land_use_m2 = Column(Float)
    
    # Quality indicators
    food_quality_rating = Column(Integer)  # 1-5 scale
    appearance_rating = Column(Integer)  # 1-5 scale
    
    # Staff information
    recorded_by = Column(String(255))  # Staff member who recorded
    verified_by = Column(String(255))  # Staff member who verified
    
    # Relationships
    sustainability_metrics = relationship("SustainabilityMetric", back_populates="waste_log")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_kg >= 0', name='check_quantity_kg_positive'),
        CheckConstraint('estimated_cost >= 0', name='check_estimated_cost_positive'),
        CheckConstraint('co2_equivalent_kg >= 0', name='check_co2_positive'),
        CheckConstraint('water_footprint_liters >= 0', name='check_water_positive'),
        CheckConstraint('land_use_m2 >= 0', name='check_land_positive'),
    )
    
    @validates('quantity_kg', 'quantity_servings', 'estimated_cost')
    def validate_quantities(self, key, value):
        """Validate quantity values."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @validates('food_quality_rating', 'appearance_rating')
    def validate_ratings(self, key, rating):
        """Validate rating values."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError(f"{key} must be between 1 and 5")
        return rating
    
    @property
    def cost_per_kg(self) -> Optional[float]:
        """Calculate cost per kilogram."""
        if self.quantity_kg and self.quantity_kg > 0:
            return (self.estimated_cost or 0) / self.quantity_kg
        return None
    
    @property
    def environmental_impact_score(self) -> float:
        """Calculate environmental impact score."""
        score = 0
        if self.co2_equivalent_kg:
            score += self.co2_equivalent_kg * 0.4
        if self.water_footprint_liters:
            score += self.water_footprint_liters * 0.001
        if self.land_use_m2:
            score += self.land_use_m2 * 0.01
        return score
    
    @classmethod
    def get_by_category(cls, session: Session, category: str, start_date: date, end_date: date) -> List['FoodWasteLog']:
        """Get waste logs by category in date range."""
        return session.query(cls).filter(
            cls.category == category,
            cls.waste_date >= start_date,
            cls.waste_date <= end_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_by_dining_hall(cls, session: Session, dining_hall: str, start_date: date, end_date: date) -> List['FoodWasteLog']:
        """Get waste logs by dining hall in date range."""
        return session.query(cls).filter(
            cls.dining_hall == dining_hall,
            cls.waste_date >= start_date,
            cls.waste_date <= end_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_top_waste_items(cls, session: Session, limit: int = 10, start_date: date = None, end_date: date = None) -> List['FoodWasteLog']:
        """Get top waste items by quantity."""
        query = session.query(cls).filter(cls.is_active == True)
        
        if start_date:
            query = query.filter(cls.waste_date >= start_date)
        if end_date:
            query = query.filter(cls.waste_date <= end_date)
        
        return query.order_by(cls.quantity_kg.desc()).limit(limit).all()


# Feedback Model
class Feedback(BaseModel):
    """User feedback model."""
    
    __tablename__ = "feedback"
    
    # User and feedback information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(100))  # e.g., food_quality, service, facility
    severity = Column(String(50))  # low, medium, high, critical
    
    # Related information
    meal_id = Column(Integer, ForeignKey("meal_logs.id"))
    waste_log_id = Column(Integer, ForeignKey("food_waste_logs.id"))
    dining_hall = Column(String(100))
    
    # Status and resolution
    status = Column(String(50), default="open")  # open, in_progress, resolved, closed
    priority = Column(String(50), default="medium")  # low, medium, high, urgent
    assigned_to = Column(String(255))  # Staff member assigned
    resolution = Column(Text)  # Resolution details
    resolved_at = Column(DateTime)
    
    # Ratings
    satisfaction_rating = Column(Integer)  # 1-5 scale for resolution satisfaction
    response_time_hours = Column(Float)  # Time to respond in hours
    
    # Relationships
    user = relationship("User", back_populates="feedback")
    meal_log = relationship("MealLog")
    waste_log = relationship("FoodWasteLog")
    
    @validates('satisfaction_rating')
    def validate_satisfaction_rating(self, key, rating):
        """Validate satisfaction rating."""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Satisfaction rating must be between 1 and 5")
        return rating
    
    @validates('response_time_hours')
    def validate_response_time(self, key, hours):
        """Validate response time."""
        if hours is not None and hours < 0:
            raise ValueError("Response time cannot be negative")
        return hours
    
    def resolve(self, resolution_text: str, assigned_to: str = None) -> None:
        """Resolve feedback."""
        self.status = "resolved"
        self.resolution = resolution_text
        self.resolved_at = datetime.utcnow()
        if assigned_to:
            self.assigned_to = assigned_to
    
    @property
    def is_overdue(self) -> bool:
        """Check if feedback is overdue for response."""
        if self.status in ["resolved", "closed"]:
            return False
        
        # Check if feedback is older than 48 hours and still open
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        return self.created_at < cutoff_time
    
    @classmethod
    def get_by_type(cls, session: Session, feedback_type: FeedbackType, start_date: date = None, end_date: date = None) -> List['Feedback']:
        """Get feedback by type."""
        query = session.query(cls).filter(
            cls.feedback_type == feedback_type,
            cls.is_active == True
        )
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        return query.all()
    
    @classmethod
    def get_overdue_feedback(cls, session: Session) -> List['Feedback']:
        """Get overdue feedback."""
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        return session.query(cls).filter(
            cls.created_at < cutoff_time,
            cls.status.in_(["open", "in_progress"]),
            cls.is_active == True
        ).all()


# Prediction Model
class Prediction(BaseModel):
    """ML prediction model for demand and waste forecasting."""
    
    __tablename__ = "predictions"
    
    # Prediction metadata
    prediction_type = Column(String(100), nullable=False)  # demand, waste, cost
    model_name = Column(String(100), nullable=False)  # xgboost, lstm, etc.
    model_version = Column(String(50))
    
    # Prediction parameters
    target_date = Column(Date, nullable=False)
    target_period = Column(String(50))  # daily, weekly, monthly
    confidence_score = Column(Float)  # 0-1 confidence interval
    
    # Prediction values
    predicted_value = Column(Float, nullable=False)
    predicted_min = Column(Float)  # Lower bound of prediction
    predicted_max = Column(Float)  # Upper bound of prediction
    
    # Context
    dining_hall = Column(String(100))
    meal_type = Column(Enum(MealType))
    food_category = Column(String(100))
    
    # Actual values (when available)
    actual_value = Column(Float)
    accuracy_score = Column(Float)  # 0-1 accuracy when actual is known
    error_percentage = Column(Float)  # Percentage error
    
    # Model parameters
    model_parameters = Column(JSON)  # Model hyperparameters
    training_data_period = Column(String(100))  # Period of training data
    features_used = Column(JSON)  # List of features used
    
    # Status
    status = Column(Enum(PredictionStatus), default=PredictionStatus.PENDING)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Relationships
    alerts = relationship("Alert", back_populates="prediction")
    
    @validates('confidence_score', 'accuracy_score')
    def validate_scores(self, key, score):
        """Validate score values."""
        if score is not None and (score < 0 or score > 1):
            raise ValueError(f"{key} must be between 0 and 1")
        return score
    
    @validates('predicted_value', 'predicted_min', 'predicted_max', 'actual_value')
    def validate_values(self, key, value):
        """Validate prediction values."""
        if value is not None and value < 0:
            raise ValueError(f"{key} cannot be negative")
        return value
    
    @property
    def is_accurate(self) -> bool:
        """Check if prediction was accurate (within 10% of actual)."""
        if self.actual_value is None or self.predicted_value is None:
            return False
        
        error_percentage = abs(self.actual_value - self.predicted_value) / self.actual_value
        return error_percentage <= 0.1
    
    @property
    def prediction_range_width(self) -> Optional[float]:
        """Calculate width of prediction range."""
        if self.predicted_min is not None and self.predicted_max is not None:
            return self.predicted_max - self.predicted_min
        return None
    
    def calculate_accuracy(self) -> None:
        """Calculate accuracy score when actual value is available."""
        if self.actual_value is not None and self.predicted_value is not None:
            if self.predicted_value > 0:
                self.error_percentage = abs(self.actual_value - self.predicted_value) / self.predicted_value
                self.accuracy_score = max(0, 1 - self.error_percentage)
    
    @classmethod
    def get_by_type_and_date(cls, session: Session, prediction_type: str, target_date: date) -> List['Prediction']:
        """Get predictions by type and date."""
        return session.query(cls).filter(
            cls.prediction_type == prediction_type,
            cls.target_date == target_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_by_model(cls, session: Session, model_name: str, start_date: date = None, end_date: date = None) -> List['Prediction']:
        """Get predictions by model."""
        query = session.query(cls).filter(
            cls.model_name == model_name,
            cls.is_active == True
        )
        
        if start_date:
            query = query.filter(cls.target_date >= start_date)
        if end_date:
            query = query.filter(cls.target_date <= end_date)
        
        return query.all()


# Alert Model
class Alert(BaseModel):
    """Alert and notification model."""
    
    __tablename__ = "alerts"
    
    # Alert information
    alert_type = Column(Enum(AlertType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    
    # Target
    user_id = Column(Integer, ForeignKey("users.id"))  # Specific user if applicable
    dining_hall = Column(String(100))  # Specific dining hall if applicable
    target_role = Column(Enum(UserRole))  # Target role if applicable
    
    # Related entities
    prediction_id = Column(Integer, ForeignKey("predictions.id"))
    waste_log_id = Column(Integer, ForeignKey("food_waste_logs.id"))
    
    # Status and handling
    status = Column(Enum(AlertStatus), default=AlertStatus.ACTIVE)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(255))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Timing
    expires_at = Column(DateTime)  # When alert expires
    auto_resolve = Column(Boolean, default=False)  # Auto-resolve when conditions change
    
    # Metadata
    source = Column(String(100))  # System, user, automated
    alert_metadata = Column(JSON)  # Additional alert data
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    prediction = relationship("Prediction", back_populates="alerts")
    waste_log = relationship("FoodWasteLog")
    
    @property
    def is_expired(self) -> bool:
        """Check if alert is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_acknowledged(self) -> bool:
        """Check if alert is acknowledged."""
        return self.acknowledged_at is not None
    
    @property
    def is_resolved(self) -> bool:
        """Check if alert is resolved."""
        return self.resolved_at is not None
    
    def acknowledge(self, acknowledged_by: str) -> None:
        """Acknowledge alert."""
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self, resolved_by: str, resolution_notes: str = None) -> None:
        """Resolve alert."""
        self.status = AlertStatus.RESOLVED
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        if resolution_notes:
            self.resolution_notes = resolution_notes
    
    def dismiss(self, dismissed_by: str) -> None:
        """Dismiss alert."""
        self.status = AlertStatus.DISMISSED
        self.resolved_by = dismissed_by
        self.resolved_at = datetime.utcnow()
        self.resolution_notes = "Alert dismissed"
    
    @classmethod
    def get_active_alerts(cls, session: Session, user_id: int = None) -> List['Alert']:
        """Get active alerts."""
        query = session.query(cls).filter(
            cls.status == AlertStatus.ACTIVE,
            cls.is_active == True
        )
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        return query.all()
    
    @classmethod
    def get_by_type(cls, session: Session, alert_type: AlertType, start_date: date = None, end_date: date = None) -> List['Alert']:
        """Get alerts by type."""
        query = session.query(cls).filter(
            cls.alert_type == alert_type,
            cls.is_active == True
        )
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
        
        return query.all()


# SustainabilityMetric Model
class SustainabilityMetric(BaseModel):
    """Sustainability metrics and KPIs model."""
    
    __tablename__ = "sustainability_metrics"
    
    # Metric information
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # waste, cost, environmental, social
    unit = Column(String(50), nullable=False)  # kg, $, co2_kg, liters, etc.
    
    # Time period
    metric_date = Column(Date, nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly, yearly
    
    # Values
    value = Column(Float, nullable=False)
    baseline_value = Column(Float)  # Baseline for comparison
    target_value = Column(Float)  # Target value
    previous_value = Column(Float)  # Previous period value
    
    # Context
    dining_hall = Column(String(100))
    category = Column(String(100))
    meal_type = Column(Enum(MealType))
    
    # Related data
    waste_log_id = Column(Integer, ForeignKey("food_waste_logs.id"))
    
    # Calculations
    percentage_change = Column(Float)  # Percentage change from baseline
    achievement_percentage = Column(Float)  # Achievement towards target
    
    # Metadata
    calculation_method = Column(String(255))
    data_source = Column(String(100))
    confidence_level = Column(Float)  # 0-1 confidence in data
    
    # Relationships
    waste_log = relationship("FoodWasteLog", back_populates="sustainability_metrics")
    
    @validates('confidence_level')
    def validate_confidence(self, key, confidence):
        """Validate confidence level."""
        if confidence is not None and (confidence < 0 or confidence > 1):
            raise ValueError("Confidence level must be between 0 and 1")
        return confidence
    
    def calculate_percentage_change(self) -> None:
        """Calculate percentage change from baseline."""
        if self.baseline_value is not None and self.baseline_value != 0:
            self.percentage_change = ((self.value - self.baseline_value) / self.baseline_value) * 100
    
    def calculate_achievement(self) -> None:
        """Calculate achievement towards target."""
        if self.target_value is not None and self.target_value != 0:
            if self.metric_type in ["waste"]:  # Lower is better
                self.achievement_percentage = max(0, min(100, 
                    ((self.baseline_value - self.value) / (self.baseline_value - self.target_value)) * 100))
            else:  # Higher is better
                self.achievement_percentage = max(0, min(100, 
                    (self.value / self.target_value) * 100))
    
    @property
    def is_improving(self) -> bool:
        """Check if metric is improving."""
        if self.previous_value is None:
            return False
        
        if self.metric_type in ["waste"]:  # Lower is better
            return self.value < self.previous_value
        else:  # Higher is better
            return self.value > self.previous_value
    
    @classmethod
    def get_by_type_and_date(cls, session: Session, metric_type: str, metric_date: date) -> List['SustainabilityMetric']:
        """Get metrics by type and date."""
        return session.query(cls).filter(
            cls.metric_type == metric_type,
            cls.metric_date == metric_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_by_dining_hall(cls, session: Session, dining_hall: str, start_date: date, end_date: date) -> List['SustainabilityMetric']:
        """Get metrics for dining hall in date range."""
        return session.query(cls).filter(
            cls.dining_hall == dining_hall,
            cls.metric_date >= start_date,
            cls.metric_date <= end_date,
            cls.is_active == True
        ).all()
    
    @classmethod
    def get_summary_metrics(cls, session: Session, metric_date: date) -> Dict[str, float]:
        """Get summary metrics for a specific date."""
        metrics = session.query(cls).filter(
            cls.metric_date == metric_date,
            cls.is_active == True
        ).all()
        
        summary = {}
        for metric in metrics:
            summary[metric.metric_name] = metric.value
        
        return summary
