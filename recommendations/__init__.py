"""
Recommendations engine for GreenPlateAI.

This module provides AI-powered recommendations for reducing
food waste through data-driven insights and actionable suggestions.
"""

from .engine import (
    get_waste_reduction_recommendations,
    generate_recommendations,
    analyze_waste_patterns,
    calculate_recommendation_priority
)
from .rules import (
    apply_business_rules,
    get_category_rules,
    get_source_rules,
    get_seasonal_rules
)
from .insights import (
    generate_insights,
    get_waste_insights,
    get_efficiency_insights,
    get_cost_insights
)

__all__ = [
    # Engine
    'get_waste_reduction_recommendations',
    'generate_recommendations',
    'analyze_waste_patterns',
    'calculate_recommendation_priority',
    
    # Rules
    'apply_business_rules',
    'get_category_rules',
    'get_source_rules',
    'get_seasonal_rules',
    
    # Insights
    'generate_insights',
    'get_waste_insights',
    'get_efficiency_insights',
    'get_cost_insights'
]
