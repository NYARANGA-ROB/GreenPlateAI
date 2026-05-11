"""
Analytics module for GreenPlateAI.

This module provides comprehensive analytics and dashboard functionality
for monitoring food waste, meal popularity, and sustainability metrics.
"""

from .data_aggregator import AnalyticsDataAggregator, get_dashboard_data, export_dashboard_summary
from .charts import AnalyticsCharts
from .dashboard import AnalyticsDashboard

__version__ = "1.0.0"
__all__ = [
    "AnalyticsDataAggregator",
    "get_dashboard_data", 
    "export_dashboard_summary",
    "AnalyticsCharts",
    "AnalyticsDashboard"
]
