"""
GreenPlateAI - University Food Waste Management System

This package provides comprehensive food waste tracking, analytics,
and sustainability management for university dining services.
"""

__version__ = "1.0.0"
__author__ = "GreenPlateAI Team"
__description__ = "University Food Waste Management System"

# Import key components
from . import database
from . import analytics
from . import models
from . import utils

__all__ = [
    "database",
    "analytics", 
    "models",
    "utils"
]
