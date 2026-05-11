"""
Input validation utilities for GreenPlateAI.

This module provides validation functions for common data types
including email, phone numbers, dates, and other business-specific
validations.
"""

import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_phone(phone: str, country_code: str = "US") -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        country_code: Country code for validation rules
        
    Returns:
        bool: True if phone is valid
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone.strip())
    
    if country_code == "US":
        # US phone numbers: 10 digits (optional country code)
        if cleaned.startswith('+1'):
            cleaned = cleaned[2:]
        return bool(re.match(r'^\d{10}$', cleaned))
    else:
        # Generic international validation: 8-15 digits
        return bool(re.match(r'^\+\d{8,15}$', cleaned) or re.match(r'^\d{8,15}$', cleaned))


def validate_date_range(start_date: Union[str, date], end_date: Union[str, date]) -> bool:
    """
    Validate date range.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        bool: True if date range is valid
    """
    try:
        # Convert string dates to date objects
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        return start_date <= end_date
    except (ValueError, TypeError):
        return False


def validate_positive_number(value: Union[str, int, float, Decimal]) -> bool:
    """
    Validate that value is a positive number.
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if value is positive
    """
    try:
        num_value = float(value)
        return num_value > 0
    except (ValueError, TypeError):
        return False


def validate_non_negative_number(value: Union[str, int, float, Decimal]) -> bool:
    """
    Validate that value is a non-negative number.
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if value is non-negative
    """
    try:
        num_value = float(value)
        return num_value >= 0
    except (ValueError, TypeError):
        return False


def validate_percentage(value: Union[str, int, float, Decimal]) -> bool:
    """
    Validate that value is a valid percentage (0-100).
    
    Args:
        value: Value to validate
        
    Returns:
        bool: True if value is valid percentage
    """
    try:
        num_value = float(value)
        return 0 <= num_value <= 100
    except (ValueError, TypeError):
        return False


def validate_weight(weight_kg: Union[str, int, float, Decimal]) -> bool:
    """
    Validate weight in kilograms.
    
    Args:
        weight_kg: Weight to validate
        
    Returns:
        bool: True if weight is valid
    """
    try:
        weight = float(weight_kg)
        return 0 <= weight <= 10000  # Max 10 tonnes
    except (ValueError, TypeError):
        return False


def validate_cost(cost: Union[str, int, float, Decimal]) -> bool:
    """
    Validate cost amount.
    
    Args:
        cost: Cost to validate
        
    Returns:
        bool: True if cost is valid
    """
    try:
        cost_value = float(cost)
        return 0 <= cost_value <= 1000000  # Max $1M
    except (ValueError, TypeError):
        return False


def validate_username(username: str) -> bool:
    """
    Validate username format.
    
    Args:
        username: Username to validate
        
    Returns:
        bool: True if username is valid
    """
    if not username or not isinstance(username, str):
        return False
    
    # Username: 3-30 characters, alphanumeric and underscores only
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return bool(re.match(pattern, username.strip()))


def validate_password_strength(password: str, min_length: int = 8) -> Dict[str, Any]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        dict: Validation result with details
    """
    result = {
        'valid': True,
        'errors': [],
        'score': 0
    }
    
    if not password or not isinstance(password, str):
        result['valid'] = False
        result['errors'].append("Password is required")
        return result
    
    password = password.strip()
    
    # Length check
    if len(password) < min_length:
        result['valid'] = False
        result['errors'].append(f"Password must be at least {min_length} characters")
    else:
        result['score'] += 1
    
    # Character variety checks
    if re.search(r'[a-z]', password):
        result['score'] += 1
    else:
        result['errors'].append("Password must contain lowercase letters")
    
    if re.search(r'[A-Z]', password):
        result['score'] += 1
    else:
        result['errors'].append("Password must contain uppercase letters")
    
    if re.search(r'\d', password):
        result['score'] += 1
    else:
        result['errors'].append("Password must contain numbers")
    
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['score'] += 1
    else:
        result['errors'].append("Password must contain special characters")
    
    # Common patterns
    common_patterns = [
        r'123456', r'password', r'qwerty', r'abc123',
        r'admin', r'letmein', r'welcome'
    ]
    
    for pattern in common_patterns:
        if re.search(pattern, password.lower()):
            result['score'] -= 1
            result['errors'].append("Password contains common patterns")
            break
    
    result['valid'] = result['valid'] and len(result['errors']) == 0
    
    return result


def validate_food_item_name(name: str) -> bool:
    """
    Validate food item name.
    
    Args:
        name: Food item name to validate
        
    Returns:
        bool: True if name is valid
    """
    if not name or not isinstance(name, str):
        return False
    
    name = name.strip()
    
    # Length: 2-200 characters
    if len(name) < 2 or len(name) > 200:
        return False
    
    # Allow letters, numbers, spaces, hyphens, and common food characters
    pattern = r'^[a-zA-Z0-9\s\-\'&(),./]+$'
    return bool(re.match(pattern, name))


def validate_sku(sku: str) -> bool:
    """
    Validate SKU format.
    
    Args:
        sku: SKU to validate
        
    Returns:
        bool: True if SKU is valid
    """
    if not sku or not isinstance(sku, str):
        return False
    
    sku = sku.strip()
    
    # SKU: 3-50 characters, alphanumeric and hyphens
    pattern = r'^[a-zA-Z0-9\-]{3,50}$'
    return bool(re.match(pattern, sku))


def validate_allergens(allergens: Union[str, List[str]]) -> bool:
    """
    Validate allergens list or JSON string.
    
    Args:
        allergens: Allergens to validate
        
    Returns:
        bool: True if allergens are valid
    """
    if not allergens:
        return True  # Empty is valid
    
    try:
        if isinstance(allergens, str):
            import json
            allergens = json.loads(allergens)
        
        if not isinstance(allergens, list):
            return False
        
        valid_allergens = [
            'milk', 'eggs', 'fish', 'shellfish', 'tree nuts', 'peanuts',
            'wheat', 'soybeans', 'sesame', 'gluten', 'lactose'
        ]
        
        for allergen in allergens:
            if not isinstance(allergen, str) or allergen.lower() not in valid_allergens:
                return False
        
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_dietary_restrictions(restrictions: Union[str, List[str]]) -> bool:
    """
    Validate dietary restrictions list or JSON string.
    
    Args:
        restrictions: Dietary restrictions to validate
        
    Returns:
        bool: True if restrictions are valid
    """
    if not restrictions:
        return True  # Empty is valid
    
    try:
        if isinstance(restrictions, str):
            import json
            restrictions = json.loads(restrictions)
        
        if not isinstance(restrictions, list):
            return False
        
        valid_restrictions = [
            'vegetarian', 'vegan', 'gluten-free', 'dairy-free',
            'nut-free', 'halal', 'kosher', 'low-sodium',
            'sugar-free', 'low-carb', 'keto', 'paleo'
        ]
        
        for restriction in restrictions:
            if not isinstance(restriction, str) or restriction.lower() not in valid_restrictions:
                return False
        
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def validate_meal_period(meal_period: str) -> bool:
    """
    Validate meal period.
    
    Args:
        meal_period: Meal period to validate
        
    Returns:
        bool: True if meal period is valid
    """
    if not meal_period or not isinstance(meal_period, str):
        return False
    
    valid_periods = ['breakfast', 'lunch', 'dinner', 'snack', 'brunch', 'late-night']
    return meal_period.lower() in valid_periods


def validate_waste_category(category: str) -> bool:
    """
    Validate waste category.
    
    Args:
        category: Waste category to validate
        
    Returns:
        bool: True if category is valid
    """
    if not category or not isinstance(category, str):
        return False
    
    valid_categories = [
        'preparation', 'spoilage', 'overproduction', 'plate_waste',
        'expired', 'damaged', 'contamination', 'other'
    ]
    return category.lower() in valid_categories


def validate_waste_source(source: str) -> bool:
    """
    Validate waste source.
    
    Args:
        source: Waste source to validate
        
    Returns:
        bool: True if source is valid
    """
    if not source or not isinstance(source, str):
        return False
    
    valid_sources = [
        'kitchen', 'dining_hall', 'catering', 'storage',
        'transport', 'events', 'other'
    ]
    return source.lower() in valid_sources


def validate_prediction_type(prediction_type: str) -> bool:
    """
    Validate prediction type.
    
    Args:
        prediction_type: Prediction type to validate
        
    Returns:
        bool: True if prediction type is valid
    """
    if not prediction_type or not isinstance(prediction_type, str):
        return False
    
    valid_types = [
        'demand_forecast', 'waste_prediction', 'inventory_optimization',
        'consumption_pattern', 'seasonal_trend'
    ]
    return prediction_type.lower() in valid_types


def validate_file_extension(filename: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validate uploaded file extension.
    
    Args:
        filename: Name of the file to validate
        allowed_extensions: List of allowed extensions (without dots)
        
    Returns:
        bool: True if file extension is valid
    """
    if not filename or not isinstance(filename, str):
        return False
    
    if allowed_extensions is None:
        allowed_extensions = ['csv', 'xlsx', 'xls', 'json']
    
    ext = Path(filename).suffix.lower().replace('.', '')
    return ext in allowed_extensions


def validate_file_size(size_bytes: int, max_size_mb: int = 50) -> bool:
    """
    Validate file size.
    
    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in MB
        
    Returns:
        bool: True if file size is valid
    """
    if not isinstance(size_bytes, int) or size_bytes < 0:
        return False
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return size_bytes <= max_size_bytes


def validate_json_structure(data: Union[str, Dict], required_fields: List[str]) -> Dict[str, Any]:
    """
    Validate JSON structure against required fields.
    
    Args:
        data: JSON string or dictionary
        required_fields: List of required field names
        
    Returns:
        dict: Validation result
    """
    result = {
        'valid': True,
        'errors': [],
        'missing_fields': []
    }
    
    try:
        if isinstance(data, str):
            import json
            data = json.loads(data)
        
        if not isinstance(data, dict):
            result['valid'] = False
            result['errors'].append("Data must be a JSON object")
            return result
        
        for field in required_fields:
            if field not in data:
                result['valid'] = False
                result['missing_fields'].append(field)
        
        if result['missing_fields']:
            result['errors'].append(f"Missing required fields: {', '.join(result['missing_fields'])}")
        
        return result
    except (json.JSONDecodeError, TypeError) as e:
        result['valid'] = False
        result['errors'].append(f"Invalid JSON format: {str(e)}")
        return result


def sanitize_string(text: str, allow_spaces: bool = True, max_length: int = None) -> str:
    """
    Sanitize string input.
    
    Args:
        text: Text to sanitize
        allow_spaces: Whether to allow spaces
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove special characters except allowed ones
    if allow_spaces:
        pattern = r'[^a-zA-Z0-9\s\-_.,:;()&/@]'
    else:
        pattern = r'[^a-zA-Z0-9\-_.,:;()&/@]'
    
    text = re.sub(pattern, '', text)
    
    # Trim to max length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_batch_number(batch_number: str) -> bool:
    """
    Validate batch number format.
    
    Args:
        batch_number: Batch number to validate
        
    Returns:
        bool: True if batch number is valid
    """
    if not batch_number or not isinstance(batch_number, str):
        return False
    
    batch_number = batch_number.strip()
    
    # Batch number: 3-50 characters, alphanumeric and hyphens
    pattern = r'^[a-zA-Z0-9\-]{3,50}$'
    return bool(re.match(pattern, batch_number))


def validate_temperature_zone(zone: str) -> bool:
    """
    Validate temperature zone.
    
    Args:
        zone: Temperature zone to validate
        
    Returns:
        bool: True if zone is valid
    """
    if not zone or not isinstance(zone, str):
        return False
    
    valid_zones = ['frozen', 'refrigerated', 'dry', 'ambient']
    return zone.lower() in valid_zones
