"""
Data validation for Food Waste Logging module.

This module provides comprehensive validation for all waste logging
forms and data inputs to ensure data integrity and consistency.
"""

import re
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import logging

from database.models import MealType, WasteCategory

logger = logging.getLogger(__name__)


class WasteLoggingValidator:
    """Validator for waste logging data."""
    
    @staticmethod
    def validate_meal_preparation_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate meal preparation data."""
        errors = []
        
        # Required fields
        required_fields = ['dining_hall', 'meal_type', 'preparation_date', 'food_items']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        # Validate dining hall
        if not isinstance(data['dining_hall'], str) or len(data['dining_hall']) < 2:
            errors.append("Dining hall must be a valid string")
        
        # Validate meal type
        try:
            MealType(data['meal_type'])
        except ValueError:
            valid_meal_types = [meal_type.value for meal_type in MealType]
            errors.append(f"Meal type must be one of: {', '.join(valid_meal_types)}")
        
        # Validate preparation date
        if isinstance(data['preparation_date'], str):
            try:
                datetime.strptime(data['preparation_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Preparation date must be in YYYY-MM-DD format")
        elif isinstance(data['preparation_date'], date):
            if data['preparation_date'] > date.today():
                errors.append("Preparation date cannot be in the future")
        else:
            errors.append("Invalid preparation date format")
        
        # Validate food items
        food_items = data['food_items']
        if not isinstance(food_items, list) or len(food_items) == 0:
            errors.append("At least one food item must be provided")
        else:
            for i, item in enumerate(food_items):
                item_errors = WasteLoggingValidator._validate_food_item(item, i)
                errors.extend(item_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_leftovers_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate leftovers data."""
        errors = []
        
        # Required fields
        required_fields = ['dining_hall', 'meal_type', 'leftovers_date', 'leftover_items']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        # Validate dining hall
        if not isinstance(data['dining_hall'], str) or len(data['dining_hall']) < 2:
            errors.append("Dining hall must be a valid string")
        
        # Validate meal type
        try:
            MealType(data['meal_type'])
        except ValueError:
            valid_meal_types = [meal_type.value for meal_type in MealType]
            errors.append(f"Meal type must be one of: {', '.join(valid_meal_types)}")
        
        # Validate leftovers date
        if isinstance(data['leftovers_date'], str):
            try:
                datetime.strptime(data['leftovers_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Leftovers date must be in YYYY-MM-DD format")
        elif isinstance(data['leftovers_date'], date):
            if data['leftovers_date'] > date.today():
                errors.append("Leftovers date cannot be in the future")
        else:
            errors.append("Invalid leftovers date format")
        
        # Validate leftover items
        leftover_items = data['leftover_items']
        if not isinstance(leftover_items, list) or len(leftover_items) == 0:
            errors.append("At least one leftover item must be provided")
        else:
            for i, item in enumerate(leftover_items):
                item_errors = WasteLoggingValidator._validate_leftover_item(item, i)
                errors.extend(item_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_disposed_food_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate disposed food data."""
        errors = []
        
        # Required fields
        required_fields = ['dining_hall', 'disposal_date', 'disposed_items']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        # Validate dining hall
        if not isinstance(data['dining_hall'], str) or len(data['dining_hall']) < 2:
            errors.append("Dining hall must be a valid string")
        
        # Validate disposal date
        if isinstance(data['disposal_date'], str):
            try:
                datetime.strptime(data['disposal_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Disposal date must be in YYYY-MM-DD format")
        elif isinstance(data['disposal_date'], date):
            if data['disposal_date'] > date.today():
                errors.append("Disposal date cannot be in the future")
        else:
            errors.append("Invalid disposal date format")
        
        # Validate disposed items
        disposed_items = data['disposed_items']
        if not isinstance(disposed_items, list) or len(disposed_items) == 0:
            errors.append("At least one disposed item must be provided")
        else:
            for i, item in enumerate(disposed_items):
                item_errors = WasteLoggingValidator._validate_disposed_item(item, i)
                errors.extend(item_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_serving_quantities_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate serving quantities data."""
        errors = []
        
        # Required fields
        required_fields = ['dining_hall', 'meal_type', 'service_date', 'serving_data']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        # Validate dining hall
        if not isinstance(data['dining_hall'], str) or len(data['dining_hall']) < 2:
            errors.append("Dining hall must be a valid string")
        
        # Validate meal type
        try:
            MealType(data['meal_type'])
        except ValueError:
            valid_meal_types = [meal_type.value for meal_type in MealType]
            errors.append(f"Meal type must be one of: {', '.join(valid_meal_types)}")
        
        # Validate service date
        if isinstance(data['service_date'], str):
            try:
                datetime.strptime(data['service_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Service date must be in YYYY-MM-DD format")
        elif isinstance(data['service_date'], date):
            if data['service_date'] > date.today():
                errors.append("Service date cannot be in the future")
        else:
            errors.append("Invalid service date format")
        
        # Validate serving data
        serving_data = data['serving_data']
        if not isinstance(serving_data, list) or len(serving_data) == 0:
            errors.append("At least one serving item must be provided")
        else:
            for i, item in enumerate(serving_data):
                item_errors = WasteLoggingValidator._validate_serving_item(item, i)
                errors.extend(item_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_daily_report_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate daily report data."""
        errors = []
        
        # Required fields
        required_fields = ['dining_hall', 'report_date', 'waste_entries']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        # Validate dining hall
        if not isinstance(data['dining_hall'], str) or len(data['dining_hall']) < 2:
            errors.append("Dining hall must be a valid string")
        
        # Validate report date
        if isinstance(data['report_date'], str):
            try:
                datetime.strptime(data['report_date'], '%Y-%m-%d')
            except ValueError:
                errors.append("Report date must be in YYYY-MM-DD format")
        elif isinstance(data['report_date'], date):
            if data['report_date'] > date.today():
                errors.append("Report date cannot be in the future")
        else:
            errors.append("Invalid report date format")
        
        # Validate waste entries
        waste_entries = data['waste_entries']
        if not isinstance(waste_entries, list) or len(waste_entries) == 0:
            errors.append("At least one waste entry must be provided")
        else:
            for i, entry in enumerate(waste_entries):
                item_errors = WasteLoggingValidator._validate_waste_entry(entry, i)
                errors.extend(item_errors)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def _validate_food_item(item: Dict[str, Any], index: int) -> List[str]:
        """Validate individual food item."""
        errors = []
        prefix = f"Food item {index + 1}:"
        
        # Required fields
        if not item.get('food_name'):
            errors.append(f"{prefix} Food name is required")
        elif not isinstance(item['food_name'], str) or len(item['food_name']) < 2:
            errors.append(f"{prefix} Food name must be at least 2 characters")
        
        if not item.get('category'):
            errors.append(f"{prefix} Category is required")
        elif item['category'] not in ["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"]:
            errors.append(f"{prefix} Invalid category")
        
        if item.get('quantity_prepared') is None:
            errors.append(f"{prefix} Quantity prepared is required")
        elif not isinstance(item['quantity_prepared'], (int, float)) or item['quantity_prepared'] <= 0:
            errors.append(f"{prefix} Quantity prepared must be greater than 0")
        elif item['quantity_prepared'] > 1000:  # Reasonable limit
            errors.append(f"{prefix} Quantity prepared seems too high (max 1000 kg)")
        
        if item.get('estimated_servings') is None:
            errors.append(f"{prefix} Estimated servings is required")
        elif not isinstance(item['estimated_servings'], int) or item['estimated_servings'] <= 0:
            errors.append(f"{prefix} Estimated servings must be greater than 0")
        elif item['estimated_servings'] > 10000:  # Reasonable limit
            errors.append(f"{prefix} Estimated servings seems too high (max 10000)")
        
        return errors
    
    @staticmethod
    def _validate_leftover_item(item: Dict[str, Any], index: int) -> List[str]:
        """Validate individual leftover item."""
        errors = []
        prefix = f"Leftover item {index + 1}:"
        
        # Required fields
        if not item.get('food_item'):
            errors.append(f"{prefix} Food item is required")
        elif not isinstance(item['food_item'], str) or len(item['food_item']) < 2:
            errors.append(f"{prefix} Food item must be at least 2 characters")
        
        if not item.get('category'):
            errors.append(f"{prefix} Category is required")
        elif item['category'] not in ["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"]:
            errors.append(f"{prefix} Invalid category")
        
        if item.get('quantity_kg') is None:
            errors.append(f"{prefix} Quantity is required")
        elif not isinstance(item['quantity_kg'], (int, float)) or item['quantity_kg'] <= 0:
            errors.append(f"{prefix} Quantity must be greater than 0")
        elif item['quantity_kg'] > 500:  # Reasonable limit
            errors.append(f"{prefix} Quantity seems too high (max 500 kg)")
        
        # Optional fields validation
        if item.get('estimated_cost') is not None:
            if not isinstance(item['estimated_cost'], (int, float)) or item['estimated_cost'] < 0:
                errors.append(f"{prefix} Estimated cost must be non-negative")
            elif item['estimated_cost'] > 10000:  # Reasonable limit
                errors.append(f"{prefix} Estimated cost seems too high (max $10000)")
        
        return errors
    
    @staticmethod
    def _validate_disposed_item(item: Dict[str, Any], index: int) -> List[str]:
        """Validate individual disposed item."""
        errors = []
        prefix = f"Disposed item {index + 1}:"
        
        # Required fields
        if not item.get('food_item'):
            errors.append(f"{prefix} Food item is required")
        elif not isinstance(item['food_item'], str) or len(item['food_item']) < 2:
            errors.append(f"{prefix} Food item must be at least 2 characters")
        
        if not item.get('category'):
            errors.append(f"{prefix} Category is required")
        elif item['category'] not in ["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"]:
            errors.append(f"{prefix} Invalid category")
        
        try:
            WasteCategory(item.get('waste_category'))
        except (ValueError, TypeError):
            valid_categories = [cat.value for cat in WasteCategory]
            errors.append(f"{prefix} Waste category must be one of: {', '.join(valid_categories)}")
        
        if item.get('quantity_kg') is None:
            errors.append(f"{prefix} Quantity is required")
        elif not isinstance(item['quantity_kg'], (int, float)) or item['quantity_kg'] <= 0:
            errors.append(f"{prefix} Quantity must be greater than 0")
        elif item['quantity_kg'] > 500:  # Reasonable limit
            errors.append(f"{prefix} Quantity seems too high (max 500 kg)")
        
        # Optional fields validation
        if item.get('estimated_cost') is not None:
            if not isinstance(item['estimated_cost'], (int, float)) or item['estimated_cost'] < 0:
                errors.append(f"{prefix} Estimated cost must be non-negative")
            elif item['estimated_cost'] > 10000:  # Reasonable limit
                errors.append(f"{prefix} Estimated cost seems too high (max $10000)")
        
        if item.get('temperature') is not None:
            if not isinstance(item['temperature'], (int, float)):
                errors.append(f"{prefix} Temperature must be a number")
            elif item['temperature'] < -50 or item['temperature'] > 100:  # Reasonable range
                errors.append(f"{prefix} Temperature seems unrealistic (-50°C to 100°C)")
        
        return errors
    
    @staticmethod
    def _validate_serving_item(item: Dict[str, Any], index: int) -> List[str]:
        """Validate individual serving item."""
        errors = []
        prefix = f"Serving item {index + 1}:"
        
        # Required fields
        if not item.get('food_item'):
            errors.append(f"{prefix} Food item is required")
        elif not isinstance(item['food_item'], str) or len(item['food_item']) < 2:
            errors.append(f"{prefix} Food item must be at least 2 characters")
        
        if not item.get('category'):
            errors.append(f"{prefix} Category is required")
        elif item['category'] not in ["Main Dish", "Side Dish", "Salad", "Dessert", "Beverage", "Other"]:
            errors.append(f"{prefix} Invalid category")
        
        if item.get('servings_prepared') is None:
            errors.append(f"{prefix} Servings prepared is required")
        elif not isinstance(item['servings_prepared'], int) or item['servings_prepared'] <= 0:
            errors.append(f"{prefix} Servings prepared must be greater than 0")
        elif item['servings_prepared'] > 10000:  # Reasonable limit
            errors.append(f"{prefix} Servings prepared seems too high (max 10000)")
        
        if item.get('servings_served') is None:
            errors.append(f"{prefix} Servings served is required")
        elif not isinstance(item['servings_served'], int) or item['servings_served'] < 0:
            errors.append(f"{prefix} Servings served must be non-negative")
        
        # Validate logical consistency
        if item.get('servings_prepared') and item.get('servings_served'):
            if item['servings_served'] > item['servings_prepared']:
                errors.append(f"{prefix} Servings served cannot exceed servings prepared")
        
        # Optional fields validation
        if item.get('serving_size_kg') is not None:
            if not isinstance(item['serving_size_kg'], (int, float)) or item['serving_size_kg'] <= 0:
                errors.append(f"{prefix} Serving size must be greater than 0")
            elif item['serving_size_kg'] > 10:  # Reasonable limit
                errors.append(f"{prefix} Serving size seems too high (max 10 kg)")
        
        if item.get('price_per_serving') is not None:
            if not isinstance(item['price_per_serving'], (int, float)) or item['price_per_serving'] < 0:
                errors.append(f"{prefix} Price per serving must be non-negative")
            elif item['price_per_serving'] > 100:  # Reasonable limit
                errors.append(f"{prefix} Price per serving seems too high (max $100)")
        
        return errors
    
    @staticmethod
    def _validate_waste_entry(entry: Dict[str, Any], index: int) -> List[str]:
        """Validate individual waste entry."""
        errors = []
        prefix = f"Waste entry {index + 1}:"
        
        # Required fields
        if not entry.get('food_item'):
            errors.append(f"{prefix} Food item is required")
        elif not isinstance(entry['food_item'], str) or len(entry['food_item']) < 2:
            errors.append(f"{prefix} Food item must be at least 2 characters")
        
        if not entry.get('category'):
            errors.append(f"{prefix} Category is required")
        elif entry['category'] not in ["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"]:
            errors.append(f"{prefix} Invalid category")
        
        try:
            WasteCategory(entry.get('waste_category'))
        except (ValueError, TypeError):
            valid_categories = [cat.value for cat in WasteCategory]
            errors.append(f"{prefix} Waste category must be one of: {', '.join(valid_categories)}")
        
        if entry.get('quantity_kg') is None:
            errors.append(f"{prefix} Quantity is required")
        elif not isinstance(entry['quantity_kg'], (int, float)) or entry['quantity_kg'] <= 0:
            errors.append(f"{prefix} Quantity must be greater than 0")
        elif entry['quantity_kg'] > 500:  # Reasonable limit
            errors.append(f"{prefix} Quantity seems too high (max 500 kg)")
        
        # Optional fields validation
        if entry.get('estimated_cost') is not None:
            if not isinstance(entry['estimated_cost'], (int, float)) or entry['estimated_cost'] < 0:
                errors.append(f"{prefix} Estimated cost must be non-negative")
            elif entry['estimated_cost'] > 10000:  # Reasonable limit
                errors.append(f"{prefix} Estimated cost seems too high (max $10000)")
        
        if entry.get('reason') and not isinstance(entry['reason'], str):
            errors.append(f"{prefix} Reason must be a string")
        
        return errors


# Convenience functions for direct use
def validate_meal_preparation_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate meal preparation data."""
    return WasteLoggingValidator.validate_meal_preparation_data(data)


def validate_leftovers_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate leftovers data."""
    return WasteLoggingValidator.validate_leftovers_data(data)


def validate_disposed_food_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate disposed food data."""
    return WasteLoggingValidator.validate_disposed_food_data(data)


def validate_serving_quantities_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate serving quantities data."""
    return WasteLoggingValidator.validate_serving_quantities_data(data)


def validate_daily_report_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate daily report data."""
    return WasteLoggingValidator.validate_daily_report_data(data)


# Additional validation utilities
class ValidationUtils:
    """Additional validation utilities."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))
    
    @staticmethod
    def validate_positive_number(value: Any, field_name: str = "Value") -> List[str]:
        """Validate positive number."""
        errors = []
        
        if value is None:
            errors.append(f"{field_name} is required")
        elif not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
        elif value <= 0:
            errors.append(f"{field_name} must be greater than 0")
        
        return errors
    
    @staticmethod
    def validate_non_negative_number(value: Any, field_name: str = "Value") -> List[str]:
        """Validate non-negative number."""
        errors = []
        
        if value is None:
            errors.append(f"{field_name} is required")
        elif not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
        elif value < 0:
            errors.append(f"{field_name} must be non-negative")
        
        return errors
    
    @staticmethod
    def validate_string(value: Any, field_name: str = "Field", min_length: int = 1, max_length: int = 255) -> List[str]:
        """Validate string field."""
        errors = []
        
        if value is None:
            errors.append(f"{field_name} is required")
        elif not isinstance(value, str):
            errors.append(f"{field_name} must be a string")
        else:
            if len(value) < min_length:
                errors.append(f"{field_name} must be at least {min_length} characters")
            if len(value) > max_length:
                errors.append(f"{field_name} must be no more than {max_length} characters")
        
        return errors
    
    @staticmethod
    def validate_date_range(start_date: date, end_date: date) -> List[str]:
        """Validate date range."""
        errors = []
        
        if start_date > end_date:
            errors.append("Start date cannot be after end date")
        
        if start_date > date.today():
            errors.append("Start date cannot be in the future")
        
        if end_date > date.today():
            errors.append("End date cannot be in the future")
        
        # Check for reasonable range (max 1 year)
        days_diff = (end_date - start_date).days
        if days_diff > 365:
            errors.append("Date range cannot exceed 1 year")
        
        return errors
    
    @staticmethod
    def validate_file_upload(file_data: Any, allowed_extensions: List[str], max_size_mb: int = 10) -> List[str]:
        """Validate uploaded file."""
        errors = []
        
        if file_data is None:
            errors.append("File is required")
            return errors
        
        # Check file size
        if hasattr(file_data, 'size'):
            size_mb = file_data.size / (1024 * 1024)
            if size_mb > max_size_mb:
                errors.append(f"File size cannot exceed {max_size_mb} MB")
        
        # Check file extension
        if hasattr(file_data, 'name'):
            file_extension = file_data.name.split('.')[-1].lower()
            if file_extension not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"File must be one of: {', '.join(allowed_extensions)}")
        
        return errors
    
    @staticmethod
    def sanitize_string(text: str) -> str:
        """Sanitize string input."""
        if not isinstance(text, str):
            return ""
        
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>"\']', '', text)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_numeric_range(value: Any, field_name: str, min_val: float = None, max_val: float = None) -> List[str]:
        """Validate numeric range."""
        errors = []
        
        if value is None:
            errors.append(f"{field_name} is required")
            return errors
        
        if not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
            return errors
        
        if min_val is not None and value < min_val:
            errors.append(f"{field_name} must be at least {min_val}")
        
        if max_val is not None and value > max_val:
            errors.append(f"{field_name} must be no more than {max_val}")
        
        return errors
