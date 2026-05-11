"""
Configuration management for GreenPlateAI.

This module provides centralized configuration management using
environment variables and default values.
"""

import os
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Application configuration class."""
    
    # Application Settings
    app_name: str = os.getenv("APP_NAME", "GreenPlateAI")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///greenplate.db")
    database_echo: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here-change-in-production")
    session_timeout_hours: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    # Authentication Configuration
    auth_enabled: bool = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    require_email_verification: bool = os.getenv("REQUIRE_EMAIL_VERIFICATION", "false").lower() == "true"
    
    # Machine Learning Configuration
    model_retraining_days: int = int(os.getenv("MODEL_RETRAINING_DAYS", "30"))
    forecasting_days_ahead: int = int(os.getenv("FORECASTING_DAYS_AHEAD", "7"))
    ml_model_path: str = os.getenv("ML_MODEL_PATH", "models/saved_models/")
    
    # Data Configuration
    data_upload_max_size_mb: int = int(os.getenv("DATA_UPLOAD_MAX_SIZE_MB", "50"))
    allowed_file_extensions: List[str] = field(
        default_factory=lambda: os.getenv("ALLOWED_FILE_EXTENSIONS", "csv,xlsx,xls").split(",")
    )
    backup_enabled: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    backup_retention_days: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    
    # External API Configuration
    weather_api_key: Optional[str] = os.getenv("WEATHER_API_KEY")
    notification_api_key: Optional[str] = os.getenv("NOTIFICATION_API_KEY")
    
    # Streamlit Configuration
    streamlit_server_port: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    streamlit_server_address: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")
    streamlit_server_headless: bool = os.getenv("STREAMLIT_SERVER_HEADLESS", "false").lower() == "true"
    streamlit_browser_gather_usage_stats: bool = os.getenv("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false").lower() == "true"
    
    # Email Configuration
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    email_from: str = os.getenv("EMAIL_FROM", "your-email@gmail.com")
    email_from_name: str = os.getenv("EMAIL_FROM_NAME", "GreenPlateAI")
    
    # University Configuration
    university_name: str = os.getenv("UNIVERSITY_NAME", "Your University")
    university_timezone: str = os.getenv("UNIVERSITY_TIMEZONE", "America/New_York")
    campus_count: int = int(os.getenv("CAMPUS_COUNT", "1"))
    dining_hall_count: int = int(os.getenv("DINING_HALL_COUNT", "3"))
    
    # Monitoring and Analytics
    enable_analytics: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")
    performance_monitoring: bool = os.getenv("PERFORMANCE_MONITORING", "true").lower() == "true"
    
    # Development Settings
    development_mode: bool = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"
    mock_external_apis: bool = os.getenv("MOCK_EXTERNAL_APIS", "false").lower() == "true"
    enable_debug_routes: bool = os.getenv("ENABLE_DEBUG_ROUTES", "false").lower() == "true"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate_config()
        
    def validate_config(self):
        """Validate critical configuration values."""
        errors = []
        
        # Check secret keys
        if self.secret_key == "your-secret-key-here-change-in-production":
            if not self.development_mode:
                errors.append("SECRET_KEY must be changed in production")
        
        if self.jwt_secret_key == "your-jwt-secret-key-here-change-in-production":
            if not self.development_mode:
                errors.append("JWT_SECRET_KEY must be changed in production")
        
        # Check database URL
        if not self.database_url:
            errors.append("DATABASE_URL is required")
        
        # Check required directories
        if self.ml_model_path and not os.path.exists(self.ml_model_path):
            try:
                os.makedirs(self.ml_model_path, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create ML model directory: {e}")
        
        # Log errors if any
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            if not self.development_mode:
                raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_database_config(self) -> dict:
        """Get database configuration as dictionary."""
        return {
            "url": self.database_url,
            "echo": self.database_echo,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True
        }
    
    def get_email_config(self) -> dict:
        """Get email configuration as dictionary."""
        return {
            "server": self.smtp_server,
            "port": self.smtp_port,
            "username": self.smtp_username,
            "password": self.smtp_password,
            "from_email": self.email_from,
            "from_name": self.email_from_name
        }
    
    def get_ml_config(self) -> dict:
        """Get machine learning configuration as dictionary."""
        return {
            "model_retraining_days": self.model_retraining_days,
            "forecasting_days_ahead": self.forecasting_days_ahead,
            "model_path": self.ml_model_path
        }
    
    def get_streamlit_config(self) -> dict:
        """Get Streamlit configuration as dictionary."""
        return {
            "server.port": self.streamlit_server_port,
            "server.address": self.streamlit_server_address,
            "server.headless": self.streamlit_server_headless,
            "browser.gatherUsageStats": self.streamlit_browser_gather_usage_stats
        }
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.development_mode
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or self.development_mode


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: Application configuration
    """
    global _config
    
    if _config is None:
        _config = Config()
        logger.info("Configuration initialized")
    
    return _config


def reload_config() -> Config:
    """
    Reload the configuration from environment variables.
    
    Returns:
        Config: Fresh configuration instance
    """
    global _config
    _config = Config()
    logger.info("Configuration reloaded")
    return _config


def update_config(**kwargs) -> Config:
    """
    Update configuration values.
    
    Args:
        **kwargs: Configuration values to update
        
    Returns:
        Config: Updated configuration
    """
    config = get_config()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
            logger.info(f"Configuration updated: {key}")
        else:
            logger.warning(f"Unknown configuration key: {key}")
    
    return config


def get_environment_info() -> dict:
    """
    Get environment information for debugging.
    
    Returns:
        dict: Environment information
    """
    config = get_config()
    
    return {
        "app_name": config.app_name,
        "app_version": config.app_version,
        "environment": "development" if config.is_development() else "production",
        "debug": config.debug,
        "database_url": config.database_url.replace(config.database_url.split("@")[0].split("//")[1] if "@" in config.database_url else "", "***") if "@" in config.database_url else "***",
        "auth_enabled": config.auth_enabled,
        "timezone": config.university_timezone,
        "python_version": os.sys.version,
        "working_directory": os.getcwd()
    }


# Configuration validation decorator
def validate_config_decorator(func):
    """Decorator to validate configuration before function execution."""
    def wrapper(*args, **kwargs):
        config = get_config()
        config.validate_config()
        return func(*args, **kwargs)
    return wrapper
