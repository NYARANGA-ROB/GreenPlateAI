"""
Business rules engine for GreenPlateAI recommendations.

This module provides rule-based filtering and prioritization
for recommendations based on business logic and constraints.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import logging

from .engine import Recommendation, Priority, RecommendationType

logger = logging.getLogger(__name__)


def apply_business_rules(
    recommendations: List[Recommendation],
    category_filter: str = None,
    source_filter: str = None,
    priority_filter: Priority = None
) -> List[Recommendation]:
    """
    Apply business rules to filter and modify recommendations.
    
    Args:
        recommendations: List of recommendations to filter
        category_filter: Filter by waste category
        source_filter: Filter by waste source
        priority_filter: Filter by priority level
        
    Returns:
        list: Filtered recommendations
    """
    try:
        filtered_recommendations = []
        
        for rec in recommendations:
            # Apply category filter
            if category_filter and rec.category != category_filter:
                continue
            
            # Apply source filter (if recommendation has source info)
            if source_filter and hasattr(rec, 'source') and rec.source != source_filter:
                continue
            
            # Apply priority filter
            if priority_filter and rec.priority != priority_filter:
                continue
            
            # Apply business logic rules
            if not meets_business_criteria(rec):
                continue
            
            # Apply resource constraints
            if not meets_resource_constraints(rec):
                continue
            
            # Apply timing rules
            if not meets_timing_requirements(rec):
                continue
            
            filtered_recommendations.append(rec)
        
        logger.info(f"Applied business rules: {len(filtered_recommendations)} recommendations remain")
        return filtered_recommendations
        
    except Exception as e:
        logger.error(f"Error applying business rules: {e}")
        return recommendations


def meets_business_criteria(recommendation: Recommendation) -> bool:
    """
    Check if recommendation meets business criteria.
    
    Args:
        recommendation: Recommendation to check
        
    Returns:
        bool: True if meets criteria
    """
    try:
        # Rule 1: High priority recommendations must have significant impact
        if recommendation.priority == Priority.HIGH and recommendation.impact == "low":
            return False
        
        # Rule 2: Recommendations must have actionable steps
        if not recommendation.action_steps or len(recommendation.action_steps) == 0:
            return False
        
        # Rule 3: Recommendations must have measurable success metrics
        if not recommendation.success_metrics or len(recommendation.success_metrics) == 0:
            return False
        
        # Rule 4: Potential savings should justify implementation effort
        if recommendation.implementation_effort == "high" and recommendation.potential_savings < 100:
            return False
        
        # Rule 5: Timeline should be reasonable for implementation effort
        if recommendation.implementation_effort == "high" and recommendation.timeline == "1 week":
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking business criteria: {e}")
        return False


def meets_resource_constraints(recommendation: Recommendation) -> bool:
    """
    Check if recommendation meets resource constraints.
    
    Args:
        recommendation: Recommendation to check
        
    Returns:
        bool: True if meets constraints
    """
    try:
        # Check if we have resources for implementation
        # This would typically check against available budget, staff, etc.
        
        # Rule 1: High effort recommendations require budget approval
        if recommendation.implementation_effort == "high":
            # In a real system, this would check budget availability
            # For now, assume we have budget for high-impact items
            if recommendation.impact == "high" and recommendation.potential_savings > 500:
                return True
            else:
                return False
        
        # Rule 2: Technology recommendations require IT resources
        if recommendation.category == "technology":
            # Check if IT resources are available
            return True  # Assume available for demo
        
        # Rule 3: Training recommendations require training budget
        if recommendation.category == "staff_training":
            return True  # Assume available for demo
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking resource constraints: {e}")
        return False


def meets_timing_requirements(recommendation: Recommendation) -> bool:
    """
    Check if recommendation meets timing requirements.
    
    Args:
        recommendation: Recommendation to check
        
    Returns:
        bool: True if meets timing requirements
    """
    try:
        # Rule 1: High priority recommendations should be implementable quickly
        if recommendation.priority == Priority.HIGH:
            max_timeline_weeks = 8
            timeline_weeks = parse_timeline_to_weeks(recommendation.timeline)
            if timeline_weeks > max_timeline_weeks:
                return False
        
        # Rule 2: Seasonal recommendations should be implemented before season
        if recommendation.category == "menu_planning":
            # Check if we're in the right season
            current_month = datetime.now().month
            # For demo, assume seasonal recommendations are always valid
            return True
        
        # Rule 3: Storage improvements should be implemented before peak season
        if recommendation.category == "storage":
            # Check if we're approaching peak usage
            return True  # Assume always valid for demo
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking timing requirements: {e}")
        return False


def get_category_rules(category: str) -> Dict[str, Any]:
    """
    Get business rules for a specific waste category.
    
    Args:
        category: Waste category
        
    Returns:
        dict: Category-specific rules
    """
    try:
        rules = {
            'overproduction': {
                'max_implementation_weeks': 6,
                'min_potential_savings': 200,
                'required_success_metrics': ['waste_reduction', 'cost_savings'],
                'priority_factors': ['volume', 'frequency', 'cost_impact']
            },
            'spoilage': {
                'max_implementation_weeks': 4,
                'min_potential_savings': 150,
                'required_success_metrics': ['spoilage_reduction', 'shelf_life_improvement'],
                'priority_factors': ['food_safety', 'cost_impact', 'frequency']
            },
            'plate_waste': {
                'max_implementation_weeks': 3,
                'min_potential_savings': 100,
                'required_success_metrics': ['plate_waste_reduction', 'student_satisfaction'],
                'priority_factors': ['student_impact', 'cost_impact', 'sustainability']
            },
            'preparation': {
                'max_implementation_weeks': 4,
                'min_potential_savings': 100,
                'required_success_metrics': ['preparation_waste_reduction', 'staff_efficiency'],
                'priority_factors': ['staff_training', 'process_improvement', 'cost_impact']
            },
            'expired': {
                'max_implementation_weeks': 2,
                'min_potential_savings': 50,
                'required_success_metrics': ['expiration_reduction', 'inventory_accuracy'],
                'priority_factors': ['food_safety', 'inventory_management', 'cost_impact']
            }
        }
        
        return rules.get(category, {})
        
    except Exception as e:
        logger.error(f"Error getting category rules: {e}")
        return {}


def get_source_rules(source: str) -> Dict[str, Any]:
    """
    Get business rules for a specific waste source.
    
    Args:
        source: Waste source
        
    Returns:
        dict: Source-specific rules
    """
    try:
        rules = {
            'kitchen': {
                'max_concurrent_recommendations': 3,
                'priority_weight': 1.2,
                'implementation_complexity': 'medium',
                'resource_requirements': ['staff', 'training', 'equipment']
            },
            'dining_hall': {
                'max_concurrent_recommendations': 2,
                'priority_weight': 1.0,
                'implementation_complexity': 'low',
                'resource_requirements': ['staff', 'communication']
            },
            'catering': {
                'max_concurrent_recommendations': 2,
                'priority_weight': 1.1,
                'implementation_complexity': 'high',
                'resource_requirements': ['staff', 'equipment', 'planning']
            },
            'storage': {
                'max_concurrent_recommendations': 1,
                'priority_weight': 1.3,
                'implementation_complexity': 'high',
                'resource_requirements': ['equipment', 'maintenance', 'monitoring']
            }
        }
        
        return rules.get(source, {})
        
    except Exception as e:
        logger.error(f"Error getting source rules: {e}")
        return {}


def get_seasonal_rules() -> Dict[str, Any]:
    """
    Get seasonal business rules.
    
    Returns:
        dict: Seasonal rules
    """
    try:
        current_month = datetime.now().month
        
        # Define seasonal rules
        seasonal_rules = {
            'spring': {  # March-May
                'focus_categories': ['preparation', 'spoilage'],
                'implementation_priority': 'medium',
                'resource_availability': 'high'
            },
            'summer': {  # June-August
                'focus_categories': ['storage', 'spoilage'],
                'implementation_priority': 'low',
                'resource_availability': 'medium'
            },
            'fall': {  # September-November
                'focus_categories': ['overproduction', 'preparation'],
                'implementation_priority': 'high',
                'resource_availability': 'high'
            },
            'winter': {  # December-February
                'focus_categories': ['storage', 'preparation'],
                'implementation_priority': 'medium',
                'resource_availability': 'high'
            }
        }
        
        # Determine current season
        if current_month in [3, 4, 5]:
            return seasonal_rules['spring']
        elif current_month in [6, 7, 8]:
            return seasonal_rules['summer']
        elif current_month in [9, 10, 11]:
            return seasonal_rules['fall']
        else:
            return seasonal_rules['winter']
        
    except Exception as e:
        logger.error(f"Error getting seasonal rules: {e}")
        return {}


def filter_by_implementation_capacity(
    recommendations: List[Recommendation],
    max_concurrent: int = 3
) -> List[Recommendation]:
    """
    Filter recommendations based on implementation capacity.
    
    Args:
        recommendations: List of recommendations
        max_concurrent: Maximum concurrent implementations
        
    Returns:
        list: Filtered recommendations
    """
    try:
        # Sort by priority and potential savings
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (x.priority.value, x.potential_savings),
            reverse=True
        )
        
        # Return top recommendations within capacity
        return sorted_recs[:max_concurrent]
        
    except Exception as e:
        logger.error(f"Error filtering by implementation capacity: {e}")
        return recommendations


def adjust_recommendation_priority(
    recommendation: Recommendation,
    contextual_factors: Dict[str, Any]
) -> Priority:
    """
    Adjust recommendation priority based on contextual factors.
    
    Args:
        recommendation: Recommendation to adjust
        contextual_factors: Contextual factors
        
    Returns:
        Priority: Adjusted priority
    """
    try:
        current_priority = recommendation.priority
        adjustment = 0
        
        # Adjust based on seasonal relevance
        if 'seasonal_relevance' in contextual_factors:
            if contextual_factors['seasonal_relevance'] == 'high':
                adjustment -= 1  # Increase priority
            elif contextual_factors['seasonal_relevance'] == 'low':
                adjustment += 1  # Decrease priority
        
        # Adjust based on resource availability
        if 'resource_availability' in contextual_factors:
            if contextual_factors['resource_availability'] == 'high':
                adjustment -= 1  # Increase priority
            elif contextual_factors['resource_availability'] == 'low':
                adjustment += 1  # Decrease priority
        
        # Adjust based on urgency
        if 'urgency' in contextual_factors:
            if contextual_factors['urgency'] == 'high':
                adjustment -= 2  # Significantly increase priority
            elif contextual_factors['urgency'] == 'low':
                adjustment += 1  # Decrease priority
        
        # Apply adjustment
        priority_levels = [Priority.LOW, Priority.MEDIUM, Priority.HIGH]
        current_index = priority_levels.index(current_priority)
        new_index = max(0, min(len(priority_levels) - 1, current_index - adjustment))
        
        return priority_levels[new_index]
        
    except Exception as e:
        logger.error(f"Error adjusting recommendation priority: {e}")
        return recommendation.priority


def validate_recommendation_completeness(recommendation: Recommendation) -> Dict[str, Any]:
    """
    Validate that a recommendation is complete and actionable.
    
    Args:
        recommendation: Recommendation to validate
        
    Returns:
        dict: Validation results
    """
    try:
        validation_results = {
            'valid': True,
            'missing_fields': [],
            'warnings': [],
            'score': 100
        }
        
        # Check required fields
        required_fields = ['title', 'description', 'category', 'priority', 'impact']
        
        for field in required_fields:
            if not hasattr(recommendation, field) or getattr(recommendation, field) is None:
                validation_results['valid'] = False
                validation_results['missing_fields'].append(field)
                validation_results['score'] -= 20
        
        # Check action steps
        if not recommendation.action_steps or len(recommendation.action_steps) == 0:
            validation_results['warnings'].append("No action steps provided")
            validation_results['score'] -= 15
        
        # Check success metrics
        if not recommendation.success_metrics or len(recommendation.success_metrics) == 0:
            validation_results['warnings'].append("No success metrics defined")
            validation_results['score'] -= 10
        
        # Check potential savings
        if recommendation.potential_savings <= 0:
            validation_results['warnings'].append("No potential savings estimated")
            validation_results['score'] -= 10
        
        # Check timeline
        if not recommendation.timeline:
            validation_results['warnings'].append("No timeline specified")
            validation_results['score'] -= 5
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating recommendation completeness: {e}")
        return {'valid': False, 'error': str(e)}


def get_recommendation_dependencies(recommendation: Recommendation) -> List[str]:
    """
    Get dependencies for a recommendation.
    
    Args:
        recommendation: Recommendation to analyze
        
    Returns:
        list: List of dependencies
    """
    try:
        dependencies = []
        
        # Category-based dependencies
        if recommendation.category == "storage":
            dependencies.extend(["inventory_system", "temperature_monitoring"])
        elif recommendation.category == "technology":
            dependencies.extend(["it_approval", "system_integration"])
        elif recommendation.category == "staff_training":
            dependencies.extend(["training_materials", "trainer_availability"])
        elif recommendation.category == "procurement":
            dependencies.extend(["supplier_contracts", "budget_approval"])
        
        # Implementation effort dependencies
        if recommendation.implementation_effort == "high":
            dependencies.extend(["budget_approval", "project_management"])
        
        return dependencies
        
    except Exception as e:
        logger.error(f"Error getting recommendation dependencies: {e}")
        return []


def estimate_implementation_timeline(recommendation: Recommendation) -> Dict[str, Any]:
    """
    Estimate detailed implementation timeline for a recommendation.
    
    Args:
        recommendation: Recommendation to analyze
        
    Returns:
        dict: Timeline estimation
    """
    try:
        base_timeline = parse_timeline_to_weeks(recommendation.timeline)
        
        # Adjust based on implementation effort
        effort_multipliers = {
            'low': 1.0,
            'medium': 1.5,
            'high': 2.0
        }
        
        multiplier = effort_multipliers.get(recommendation.implementation_effort, 1.0)
        adjusted_weeks = int(base_timeline * multiplier)
        
        # Break down into phases
        phases = {
            'planning': max(1, int(adjusted_weeks * 0.2)),
            'implementation': max(1, int(adjusted_weeks * 0.6)),
            'testing': max(1, int(adjusted_weeks * 0.15)),
            'deployment': max(1, int(adjusted_weeks * 0.05))
        }
        
        return {
            'total_weeks': adjusted_weeks,
            'phases': phases,
            'estimated_completion': datetime.now() + timedelta(weeks=adjusted_weeks),
            'confidence_level': 'high' if recommendation.implementation_effort == 'low' else 'medium'
        }
        
    except Exception as e:
        logger.error(f"Error estimating implementation timeline: {e}")
        return {'total_weeks': 4, 'phases': {}, 'error': str(e)}


# Helper functions

def parse_timeline_to_weeks(timeline: str) -> int:
    """Parse timeline string to weeks."""
    try:
        if 'week' in timeline.lower():
            # Extract number from timeline
            import re
            match = re.search(r'(\d+)', timeline)
            if match:
                return int(match.group(1))
        elif 'month' in timeline.lower():
            match = re.search(r'(\d+)', timeline)
            if match:
                return int(match.group(1)) * 4
        elif 'day' in timeline.lower():
            match = re.search(r'(\d+)', timeline)
            if match:
                return max(1, int(match.group(1)) // 7)
        
        # Default to 4 weeks if can't parse
        return 4
        
    except Exception as e:
        logger.error(f"Error parsing timeline: {e}")
        return 4


def calculate_recommendation_score(recommendation: Recommendation) -> float:
    """
    Calculate overall recommendation score.
    
    Args:
        recommendation: Recommendation to score
        
    Returns:
        float: Score (0-100)
    """
    try:
        score = 0.0
        
        # Priority score (0-30)
        priority_scores = {Priority.HIGH: 30, Priority.MEDIUM: 20, Priority.LOW: 10}
        score += priority_scores.get(recommendation.priority, 15)
        
        # Impact score (0-25)
        impact_scores = {'high': 25, 'medium': 15, 'low': 5}
        score += impact_scores.get(recommendation.impact, 15)
        
        # Potential savings score (0-25)
        if recommendation.potential_savings >= 1000:
            score += 25
        elif recommendation.potential_savings >= 500:
            score += 20
        elif recommendation.potential_savings >= 100:
            score += 15
        elif recommendation.potential_savings >= 50:
            score += 10
        else:
            score += 5
        
        # Implementation effort penalty (0-20)
        effort_penalties = {'low': 0, 'medium': -5, 'high': -10}
        score += effort_penalties.get(recommendation.implementation_effort, -5)
        
        return max(0, min(100, score))
        
    except Exception as e:
        logger.error(f"Error calculating recommendation score: {e}")
        return 50.0
