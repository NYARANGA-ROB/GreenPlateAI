"""
Food item and inventory management models.

This module contains models for food items, categories, inventory tracking,
and menu items for the university dining system.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseModel


class FoodCategory(BaseModel):
    """Food category model for organizing food items."""
    
    __tablename__ = "food_categories"
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    color_code = Column(String(7))  # Hex color for UI
    icon = Column(String(50))  # Icon name for UI
    parent_category_id = Column(Integer, ForeignKey("food_categories.id"))
    sort_order = Column(Integer, default=0)
    
    # Relationships
    parent_category = relationship("FoodCategory", remote_side="FoodCategory.id")
    sub_categories = relationship("FoodCategory", back_populates="parent_category")
    food_items = relationship("FoodItem", back_populates="category")
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """Convert category to dictionary with sub-categories."""
        result = super().to_dict(exclude_fields=exclude_fields)
        if 'food_items' not in (exclude_fields or []):
            result['food_items_count'] = len([item for item in self.food_items if item.is_active])
        return result


class FoodItem(BaseModel):
    """Food item model for individual food products."""
    
    __tablename__ = "food_items"
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("food_categories.id"), nullable=False)
    sku = Column(String(50), unique=True, index=True)
    barcode = Column(String(50))
    unit_of_measure = Column(String(20), default="pieces")
    cost_per_unit = Column(Numeric(10, 2))
    selling_price_per_unit = Column(Numeric(10, 2))
    calories_per_unit = Column(Integer)
    allergens = Column(Text)  # JSON array of allergens
    dietary_restrictions = Column(Text)  # JSON array of restrictions
    storage_requirements = Column(Text)
    shelf_life_days = Column(Integer)
    minimum_order_quantity = Column(Integer, default=1)
    maximum_order_quantity = Column(Integer)
    supplier_name = Column(String(200))
    supplier_contact = Column(String(500))
    nutritional_info = Column(Text)  # JSON object with nutritional data
    preparation_instructions = Column(Text)
    serving_size = Column(String(50))
    image_url = Column(String(500))
    tags = Column(Text)  # JSON array of tags
    
    # Relationships
    category = relationship("FoodCategory", back_populates="food_items")
    inventory_items = relationship("Inventory", back_populates="food_item")
    menu_items = relationship("MenuItem", back_populates="food_item")
    
    @property
    def current_stock(self) -> int:
        """Get current stock quantity."""
        total_stock = sum(
            inv.quantity for inv in self.inventory_items 
            if inv.is_active and not inv.is_expired
        )
        return total_stock
    
    @property
    def total_value(self) -> Decimal:
        """Get total value of current stock."""
        return self.current_stock * (self.cost_per_unit or Decimal('0'))
    
    @property
    def is_low_stock(self) -> bool:
        """Check if item is low stock."""
        return self.current_stock < (self.minimum_order_quantity or 0)
    
    @property
    def is_expired_stock(self) -> bool:
        """Check if any stock is expired."""
        return any(inv.is_expired for inv in self.inventory_items if inv.is_active)
    
    def get_allergen_list(self) -> list:
        """Get list of allergens."""
        if not self.allergens:
            return []
        # Parse JSON string (simplified - in production use proper JSON parsing)
        try:
            import json
            return json.loads(self.allergens)
        except:
            return []
    
    def get_dietary_restrictions_list(self) -> list:
        """Get list of dietary restrictions."""
        if not self.dietary_restrictions:
            return []
        try:
            import json
            return json.loads(self.dietary_restrictions)
        except:
            return []


class Inventory(BaseModel):
    """Inventory tracking model for food items."""
    
    __tablename__ = "inventory"
    
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    batch_number = Column(String(50))
    received_date = Column(DateTime, default=datetime.utcnow)
    expiration_date = Column(DateTime)
    storage_location = Column(String(100))
    temperature_zone = Column(String(20))  # frozen, refrigerated, dry
    quality_grade = Column(String(20))  # A, B, C
    supplier_batch_id = Column(String(50))
    cost_per_unit = Column(Numeric(10, 2))
    notes = Column(Text)
    last_counted = Column(DateTime)
    variance_quantity = Column(Integer, default=0)
    variance_reason = Column(String(200))
    
    # Relationships
    food_item = relationship("FoodItem", back_populates="inventory_items")
    
    @property
    def is_expired(self) -> bool:
        """Check if inventory item is expired."""
        if not self.expiration_date:
            return False
        return datetime.utcnow() > self.expiration_date
    
    @property
    def days_until_expiration(self) -> int:
        """Get days until expiration."""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_near_expiration(self, days_threshold: int = 7) -> bool:
        """Check if item is near expiration."""
        if not self.expiration_date:
            return False
        return self.days_until_expiration <= days_threshold
    
    @property
    def total_value(self) -> Decimal:
        """Get total value of inventory item."""
        return self.quantity * (self.cost_per_unit or Decimal('0'))
    
    def adjust_quantity(self, new_quantity: int, reason: str = None) -> None:
        """Adjust inventory quantity."""
        old_quantity = self.quantity
        self.quantity = new_quantity
        self.variance_quantity = new_quantity - old_quantity
        self.variance_reason = reason
        self.last_counted = datetime.utcnow()


class MenuItem(BaseModel):
    """Menu item model for dining hall menus."""
    
    __tablename__ = "menu_items"
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    recipe_instructions = Column(Text)
    preparation_time_minutes = Column(Integer)
    serving_size = Column(String(50))
    price = Column(Numeric(10, 2))
    is_available = Column(Boolean, default=True)
    is_seasonal = Column(Boolean, default=False)
    season_start = Column(DateTime)
    season_end = Column(DateTime)
    meal_period = Column(String(20))  # breakfast, lunch, dinner, snack
    cuisine_type = Column(String(50))
    spice_level = Column(String(10))  # mild, medium, hot
    popularity_score = Column(Integer, default=0)
    dietary_type = Column(String(50))  # vegetarian, vegan, gluten-free, etc.
    image_url = Column(String(500))
    allergen_warning = Column(Text)
    nutritional_info = Column(Text)  # JSON object
    
    # Relationships
    food_item = relationship("FoodItem", back_populates="menu_items")
    
    @property
    def is_in_season(self) -> bool:
        """Check if menu item is currently in season."""
        if not self.is_seasonal:
            return True
        if not self.season_start or not self.season_end:
            return True
        now = datetime.utcnow()
        return self.season_start <= now <= self.season_end
    
    @property
    def can_be_served(self) -> bool:
        """Check if menu item can be served."""
        return self.is_available and self.is_in_season
