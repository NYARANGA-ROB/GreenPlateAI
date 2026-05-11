"""
Base model class for all SQLAlchemy models.

This module provides the base model with common fields and functionality
that all other models will inherit from.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.ext.declarative import declared_attr

from database.connection import Base


class BaseModel(Base):
    """Base model class with common fields and functionality."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name."""
        return cls.__name__.lower()
    
    def to_dict(self, exclude_fields: list = None) -> dict:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude_fields: List of fields to exclude from the dictionary
            
        Returns:
            dict: Model data as dictionary
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude_fields:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
                
        return result
    
    def update_from_dict(self, data: dict, exclude_fields: list = None) -> None:
        """
        Update model instance from dictionary data.
        
        Args:
            data: Dictionary with field values
            exclude_fields: List of fields to exclude from updating
        """
        exclude_fields = exclude_fields or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def soft_delete(self) -> None:
        """Soft delete the model instance."""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft deleted model instance."""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
