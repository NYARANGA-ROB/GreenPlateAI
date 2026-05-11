"""
General helper functions for GreenPlateAI.

This module provides various utility functions for common operations
including password hashing, token generation, formatting, calculations,
and data manipulation.
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, Dict, Any, List, Union
import json
import logging
from pytz import timezone
import pandas as pd
import numpy as np

from .config import get_config

logger = logging.getLogger(__name__)


def get_client_ip(default: str = "127.0.0.1") -> str:
    """
    Best-effort client IP accessor for Streamlit sessions.

    Returns a default local address when request context is unavailable.
    """
    try:
        import streamlit as st

        ctx = getattr(st, "context", None)
        if ctx and getattr(ctx, "ip_address", None):
            return str(ctx.ip_address)
    except Exception:
        pass

    return default


def get_user_agent(default: str = "streamlit-client") -> str:
    """
    Best-effort user agent accessor for Streamlit sessions.

    Returns a generic user agent when request context is unavailable.
    """
    try:
        import streamlit as st

        ctx = getattr(st, "context", None)
        if ctx and getattr(ctx, "headers", None):
            user_agent = ctx.headers.get("User-Agent")
            if user_agent:
                return str(user_agent)
    except Exception:
        pass

    return default


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 with salt.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    try:
        import bcrypt
        # Use bcrypt for better security
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except ImportError:
        # Fallback to SHA-256 if bcrypt not available
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${password_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password
        
    Returns:
        bool: True if password matches
    """
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except ImportError:
        # Fallback for SHA-256
        try:
            salt, password_hash = hashed.split('$')
            test_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return test_hash == password_hash
        except ValueError:
            return False


def generate_token(user_id: str, expires_hours: int = 24) -> str:
    """
    Generate JWT token for authentication.
    
    Args:
        user_id: User identifier
        expires_hours: Token expiration in hours
        
    Returns:
        str: JWT token
    """
    config = get_config()
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=expires_hours),
        'iat': datetime.utcnow(),
        'iss': config.app_name
    }
    
    return jwt.encode(payload, config.jwt_secret_key, algorithm='HS256')


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload.
    
    Args:
        token: JWT token
        
    Returns:
        dict: Token payload if valid, None otherwise
    """
    config = get_config()
    
    try:
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def format_currency(amount: Union[float, Decimal], currency: str = "$") -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency symbol
        
    Returns:
        str: Formatted currency string
    """
    if amount is None:
        return f"{currency}0.00"
    
    return f"{currency}{float(amount):,.2f}"


def format_weight(weight_kg: Union[float, Decimal], precision: int = 2) -> str:
    """
    Format weight in kilograms with appropriate units.
    
    Args:
        weight_kg: Weight in kilograms
        precision: Decimal precision
        
    Returns:
        str: Formatted weight string
    """
    if weight_kg is None:
        return "0 kg"
    
    weight = float(weight_kg)
    
    if weight >= 1000:
        return f"{weight/1000:.{precision}f} tonnes"
    elif weight >= 1:
        return f"{weight:.{precision}f} kg"
    elif weight >= 0.001:
        return f"{weight*1000:.{precision}f} g"
    else:
        return f"{weight*1000000:.{precision}f} mg"


def format_percentage(value: Union[float, Decimal], total: Union[float, Decimal] = None) -> str:
    """
    Format value as percentage.
    
    Args:
        value: Value to format
        total: Total value for percentage calculation
        
    Returns:
        str: Formatted percentage string
    """
    if value is None:
        return "0%"
    
    if total is not None and total != 0:
        percentage = (float(value) / float(total)) * 100
    else:
        percentage = float(value)
    
    return f"{percentage:.1f}%"


def calculate_co2_equivalent(weight_kg: Union[float, Decimal]) -> float:
    """
    Calculate CO2 equivalent for food waste.
    
    Args:
        weight_kg: Weight in kilograms
        
    Returns:
        float: CO2 equivalent in kg
    """
    if weight_kg is None:
        return 0.0
    
    # Rough estimate: 2.3 kg CO2 per kg of food waste
    # This varies by food type but provides a general estimate
    return float(weight_kg) * 2.3


def calculate_water_footprint(weight_kg: Union[float, Decimal]) -> float:
    """
    Calculate water footprint for food waste.
    
    Args:
        weight_kg: Weight in kilograms
        
    Returns:
        float: Water footprint in liters
    """
    if weight_kg is None:
        return 0.0
    
    # Rough estimate: 1000 liters per kg of food waste
    # This varies significantly by food type
    return float(weight_kg) * 1000


def get_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Get list of dates between start and end date.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        list: List of dates
    """
    if start_date > end_date:
        return []
    
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def safe_get_nested_dict(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Safely get value from nested dictionary using dot notation.
    
    Args:
        data: Dictionary to search
        key_path: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely dump object to JSON string.
    
    Args:
        obj: Object to serialize
        default: Default string if serialization fails
        
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def convert_to_utc(dt: datetime, tz_name: str = None) -> datetime:
    """
    Convert datetime to UTC.
    
    Args:
        dt: Datetime to convert
        tz_name: Timezone name (uses config default if None)
        
    Returns:
        datetime: UTC datetime
    """
    if dt is None:
        return None
    
    config = get_config()
    tz_name = tz_name or config.university_timezone
    
    try:
        local_tz = timezone(tz_name)
        if dt.tzinfo is None:
            dt = local_tz.localize(dt)
        return dt.astimezone(timezone('UTC'))
    except Exception as e:
        logger.warning(f"Timezone conversion failed: {e}")
        return dt


def convert_from_utc(dt: datetime, tz_name: str = None) -> datetime:
    """
    Convert datetime from UTC to local timezone.
    
    Args:
        dt: UTC datetime to convert
        tz_name: Target timezone name
        
    Returns:
        datetime: Local datetime
    """
    if dt is None:
        return None
    
    config = get_config()
    tz_name = tz_name or config.university_timezone
    
    try:
        if dt.tzinfo is None:
            dt = timezone('UTC').localize(dt)
        return dt.astimezone(timezone(tz_name))
    except Exception as e:
        logger.warning(f"Timezone conversion failed: {e}")
        return dt


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate unique identifier.
    
    Args:
        prefix: Optional prefix for the ID
        
    Returns:
        str: Unique identifier
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4)
    return f"{prefix}{timestamp}{random_part}"


def clean_numeric_string(value: str, default: float = 0.0) -> float:
    """
    Clean numeric string and convert to float.
    
    Args:
        value: String to clean
        default: Default value if conversion fails
        
    Returns:
        float: Cleaned numeric value
    """
    if value is None:
        return default
    
    try:
        # Remove common non-numeric characters
        cleaned = str(value).replace(',', '').replace('$', '').replace('%', '').strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def calculate_growth_rate(current: float, previous: float) -> float:
    """
    Calculate growth rate between two values.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        float: Growth rate as percentage
    """
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    
    return ((current - previous) / previous) * 100


def moving_average(data: List[float], window: int) -> List[float]:
    """
    Calculate moving average for data series.
    
    Args:
        data: List of numeric values
        window: Window size for moving average
        
    Returns:
        list: Moving average values
    """
    if not data or window <= 0:
        return []
    
    if len(data) < window:
        return [sum(data) / len(data)] * len(data)
    
    result = []
    for i in range(len(data)):
        start_idx = max(0, i - window + 1)
        window_data = data[start_idx:i + 1]
        result.append(sum(window_data) / len(window_data))
    
    return result


def detect_outliers(data: List[float], threshold: float = 2.0) -> List[int]:
    """
    Detect outliers in data using z-score method.
    
    Args:
        data: List of numeric values
        threshold: Z-score threshold for outlier detection
        
    Returns:
        list: Indices of outliers
    """
    if not data or len(data) < 3:
        return []
    
    try:
        data_array = np.array(data)
        mean = np.mean(data_array)
        std = np.std(data_array)
        
        if std == 0:
            return []
        
        z_scores = np.abs((data_array - mean) / std)
        outlier_indices = np.where(z_scores > threshold)[0].tolist()
        
        return outlier_indices
    except Exception as e:
        logger.warning(f"Outlier detection failed: {e}")
        return []


def aggregate_data_by_period(
    data: pd.DataFrame,
    date_column: str,
    value_column: str,
    period: str = 'daily'
) -> pd.DataFrame:
    """
    Aggregate data by time period.
    
    Args:
        data: DataFrame with date and value columns
        date_column: Name of date column
        value_column: Name of value column
        period: Aggregation period (daily, weekly, monthly)
        
    Returns:
        DataFrame: Aggregated data
    """
    if data.empty:
        return pd.DataFrame()
    
    try:
        df = data.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        if period == 'daily':
            df = df.groupby(df[date_column].dt.date).agg({value_column: ['sum', 'mean', 'count']})
        elif period == 'weekly':
            df = df.groupby(df[date_column].dt.to_period('W')).agg({value_column: ['sum', 'mean', 'count']})
        elif period == 'monthly':
            df = df.groupby(df[date_column].dt.to_period('M')).agg({value_column: ['sum', 'mean', 'count']})
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        # Flatten column names
        df.columns = ['_'.join(col).strip() for col in df.columns]
        df = df.reset_index()
        
        return df
    except Exception as e:
        logger.error(f"Data aggregation failed: {e}")
        return pd.DataFrame()


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension against allowed list.
    
    Args:
        filename: File name to validate
        allowed_extensions: List of allowed extensions
        
    Returns:
        bool: True if extension is allowed
    """
    if not filename or '.' not in filename:
        return False
    
    extension = filename.split('.')[-1].lower()
    return extension in [ext.lower().lstrip('.') for ext in allowed_extensions]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix
