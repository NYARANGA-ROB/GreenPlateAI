"""
Food waste tracking and analysis models.

This module contains models for recording, categorizing, and analyzing
food waste data in the university dining system.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class WasteCategory(str, Enum):
    """Categories of food waste."""
    PREPARATION = "preparation"
    SPOILAGE = "spoilage"
    OVERPRODUCTION = "overproduction"
    PLATE_WASTE = "plate_waste"
    EXPIRED = "expired"
    DAMAGED = "damaged"
    CONTAMINATION = "contamination"
    OTHER = "other"


class WasteSource(str, Enum):
    """Sources of food waste."""
    KITCHEN = "kitchen"
    DINING_HALL = "dining_hall"
    CATERING = "catering"
    STORAGE = "storage"
    TRANSPORT = "transport"
    EVENTS = "events"


class WasteRecord(BaseModel):
    """Main waste record model for tracking food waste."""
    
    __tablename__ = "waste_records"
    
    date = Column(Date, nullable=False, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    category = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)
    quantity_kg = Column(Numeric(10, 3), nullable=False)
    estimated_cost = Column(Numeric(10, 2))
    meal_period = Column(String(20))  # breakfast, lunch, dinner, snack
    dining_hall = Column(String(100))
    recorded_by = Column(String(50))  # User ID who recorded the waste
    verified = Column(Boolean, default=False)
    verified_by = Column(String(50))
    verified_at = Column(DateTime)
    notes = Column(Text)
    prevention_measures = Column(Text)
    image_url = Column(String(500))
    temperature_at_disposal = Column(Numeric(5, 2))  # Celsius
    disposal_method = Column(String(50))  # compost, landfill, donation, etc.
    batch_number = Column(String(50))
    preparation_time = Column(DateTime)
    service_time = Column(DateTime)
    waste_reason_code = Column(String(20))  # Standardized waste reason codes
    preventable = Column(Boolean, default=True)
    severity_score = Column(Integer, default=1)  # 1-5 scale
    
    # Relationships
    food_item = relationship("FoodItem")
    
    @property
    def cost_per_kg(self) -> Decimal:
        """Calculate cost per kilogram of waste."""
        if self.quantity_kg and self.quantity_kg > 0:
            return (self.estimated_cost or Decimal('0')) / self.quantity_kg
        return Decimal('0')
    
    @property
    def co2_equivalent_kg(self) -> Decimal:
        """Calculate CO2 equivalent (rough estimate)."""
        # Rough estimate: 2.3 kg CO2 per kg of food waste
        return self.quantity_kg * Decimal('2.3')
    
    @property
    def water_footprint_liters(self) -> Decimal:
        """Calculate water footprint (rough estimate)."""
        # Rough estimate: 1000 liters per kg of food waste
        return self.quantity_kg * Decimal('1000')
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """Convert waste record to dictionary with calculated fields."""
        result = super().to_dict(exclude_fields=exclude_fields)
        result.update({
            'cost_per_kg': float(self.cost_per_kg),
            'co2_equivalent_kg': float(self.co2_equivalent_kg),
            'water_footprint_liters': float(self.water_footprint_liters)
        })
        return result


class WasteAnalysis(BaseModel):
    """Waste analysis model for aggregated insights."""
    
    __tablename__ = "waste_analysis"
    
    analysis_date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    total_waste_kg = Column(Numeric(10, 3), nullable=False)
    total_cost = Column(Numeric(10, 2), nullable=False)
    total_records = Column(Integer, nullable=False)
    top_waste_category = Column(String(50))
    top_waste_source = Column(String(50))
    top_food_item_id = Column(Integer)
    average_waste_per_record = Column(Numeric(10, 3))
    waste_trend = Column(String(20))  # increasing, decreasing, stable
    trend_percentage = Column(Numeric(5, 2))
    preventable_percentage = Column(Numeric(5, 2))
    insights = Column(Text)  # JSON object with analysis insights
    recommendations = Column(Text)  # JSON array of recommendations
    
    @property
    def average_cost_per_record(self) -> Decimal:
        """Calculate average cost per waste record."""
        if self.total_records and self.total_records > 0:
            return self.total_cost / self.total_records
        return Decimal('0')


class WasteTarget(BaseModel):
    """Waste reduction targets and goals."""
    
    __tablename__ = "waste_targets"
    
    target_name = Column(String(200), nullable=False)
    description = Column(Text)
    target_type = Column(String(50), nullable=False)  # overall, category, source, item
    target_reference_id = Column(Integer)  # ID for category/source/item targets
    baseline_waste_kg = Column(Numeric(10, 3), nullable=False)
    target_waste_kg = Column(Numeric(10, 3), nullable=False)
    reduction_percentage = Column(Numeric(5, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    current_waste_kg = Column(Numeric(10, 3))
    progress_percentage = Column(Numeric(5, 2))
    status = Column(String(20), default="active")  # active, completed, failed
    assigned_to = Column(String(50))  # User ID responsible
    created_by = Column(String(50))
    
    @property
    def is_achieved(self) -> bool:
        """Check if target is achieved."""
        if self.current_waste_kg is None:
            return False
        return self.current_waste_kg <= self.target_waste_kg
    
    @property
    def days_remaining(self) -> int:
        """Calculate days remaining until target deadline."""
        if not self.end_date:
            return 0
        delta = self.end_date - date.today()
        return max(0, delta.days)
    
    @property
    def is_overdue(self) -> bool:
        """Check if target is overdue."""
        if not self.end_date:
            return False
        return date.today() > self.end_date and not self.is_achieved
    
    def update_progress(self, current_waste_kg: Decimal) -> None:
        """Update target progress."""
        self.current_waste_kg = current_waste_kg
        if self.baseline_waste_kg > 0:
            reduction = self.baseline_waste_kg - current_waste_kg
            self.progress_percentage = (reduction / self.baseline_waste_kg) * 100
        
        # Update status if achieved
        if self.is_achieved:
            self.status = "completed"


class WastePreventionAction(BaseModel):
    """Waste prevention actions and interventions."""
    
    __tablename__ = "waste_prevention_actions"
    
    action_name = Column(String(200), nullable=False)
    description = Column(Text)
    action_type = Column(String(50), nullable=False)  # process, training, equipment, policy
    target_category = Column(String(50))
    target_source = Column(String(50))
    implementation_date = Column(Date)
    estimated_impact_kg = Column(Numeric(10, 3))
    actual_impact_kg = Column(Numeric(10, 3))
    cost_of_implementation = Column(Numeric(10, 2))
    savings_per_month = Column(Numeric(10, 2))
    roi_months = Column(Integer)
    status = Column(String(20), default="planned")  # planned, active, completed, cancelled
    priority = Column(String(10), default="medium")  # low, medium, high
    assigned_to = Column(String(50))
    created_by = Column(String(50))
    completion_date = Column(Date)
    effectiveness_score = Column(Integer)  # 1-5 scale
    lessons_learned = Column(Text)
    next_review_date = Column(Date)
    
    @property
    def is_active(self) -> bool:
        """Check if action is currently active."""
        return self.status == "active"
    
    @property
    def roi_months_calculated(self) -> Optional[int]:
        """Calculate return on investment in months."""
        if self.cost_of_implementation and self.savings_per_month and self.savings_per_month > 0:
            return int(self.cost_of_implementation / self.savings_per_month)
        return None
    
    @property
    def is_effective(self) -> bool:
        """Check if action is effective based on impact."""
        if self.actual_impact_kg is None or self.estimated_impact_kg is None:
            return False
        return self.actual_impact_kg >= (self.estimated_impact_kg * Decimal('0.8'))
