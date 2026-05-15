"""
Core recommendations engine for GreenPlateAI.
This module provides the main recommendation generation logic,
pattern analysis, and priority calculation for waste reduction.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

from database.connection import get_session
from models.waste_record import WasteRecord
from models.food_item import FoodItem
from utils.helpers import format_currency, format_weight, format_percentage

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    """Types of recommendations."""
    PREPARATION = "preparation"
    STORAGE = "storage"
    MENU_PLANNING = "menu_planning"
    PROCUREMENT = "procurement"
    STAFF_TRAINING = "staff_training"
    TECHNOLOGY = "technology"
    MONITORING = "monitoring"
    POLICY = "policy"


class Priority(str, Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Recommendation:
    """Recommendation data structure."""
    title: str
    description: str
    category: str
    priority: Priority
    impact: str
    action_steps: List[str]
    potential_savings: float
    implementation_effort: str
    timeline: str
    success_metrics: List[str]
    supporting_data: Dict[str, Any]


def get_waste_reduction_recommendations(
    category: str = None,
    source: str = None,
    priority: Priority = None,
    days_back: int = 30
) -> List[Dict[str, Any]]:
    """
    Get waste reduction recommendations based on data analysis.
    
    Args:
        category: Filter by waste category
        source: Filter by waste source
        priority: Filter by priority level
        days_back: Number of days to analyze
        
    Returns:
        list: Recommendation data
    """
    try:
        logger.info(f"Generating recommendations for category: {category}, source: {source}")
        
        # Analyze waste patterns
        patterns = analyze_waste_patterns(days_back)
        
        # Generate base recommendations
        base_recommendations = generate_base_recommendations(patterns, category, source)
        
        # Apply business rules
        filtered_recommendations = apply_business_rules(base_recommendations, category, source, priority)
        
        # Calculate priority scores
        prioritized_recommendations = []
        for rec in filtered_recommendations:
            priority_score = calculate_recommendation_priority(rec, patterns)
            rec['priority_score'] = priority_score
            prioritized_recommendations.append(rec)
        
        # Sort by priority score
        prioritized_recommendations.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Convert to dict format
        result = []
        for rec in prioritized_recommendations:
            result.append({
                'title': rec.title,
                'description': rec.description,
                'category': rec.category,
                'priority': rec.priority.value,
                'impact': rec.impact,
                'action_steps': rec.action_steps,
                'potential_savings': rec.potential_savings,
                'implementation_effort': rec.implementation_effort,
                'timeline': rec.timeline,
                'success_metrics': rec.success_metrics,
                'supporting_data': rec.supporting_data
            })
        
        logger.info(f"Generated {len(result)} recommendations")
        return result
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []


def generate_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """
    Generate recommendations based on waste patterns.
    
    Args:
        patterns: Analyzed waste patterns
        
    Returns:
        list: Recommendation objects
    """
    try:
        recommendations = []
        
        # Overproduction recommendations
        if patterns.get('overproduction_detected', False):
            recommendations.extend(generate_overproduction_recommendations(patterns))
        
        # Spoilage recommendations
        if patterns.get('spoilage_detected', False):
            recommendations.extend(generate_spoilage_recommendations(patterns))
        
        # Plate waste recommendations
        if patterns.get('plate_waste_detected', False):
            recommendations.extend(generate_plate_waste_recommendations(patterns))
        
        # Storage recommendations
        if patterns.get('storage_issues_detected', False):
            recommendations.extend(generate_storage_recommendations(patterns))
        
        # Preparation recommendations
        if patterns.get('preparation_issues_detected', False):
            recommendations.extend(generate_preparation_recommendations(patterns))
        
        # Seasonal recommendations
        if patterns.get('seasonal_patterns_detected', False):
            recommendations.extend(generate_seasonal_recommendations(patterns))
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []


def analyze_waste_patterns(days_back: int = 30) -> Dict[str, Any]:
    """
    Analyze waste patterns to inform recommendations.
    
    Args:
        days_back: Number of days to analyze
        
    Returns:
        dict: Pattern analysis results
    """
    try:
        # Get waste data
        waste_data = get_waste_data(days_back)
        
        if waste_data.empty:
            return get_empty_patterns()
        
        patterns = {
            'total_waste_kg': waste_data['quantity_kg'].sum(),
            'total_cost': waste_data['estimated_cost'].sum(),
            'avg_daily_waste': waste_data['quantity_kg'].sum() / days_back,
            'category_breakdown': analyze_category_patterns(waste_data),
            'source_breakdown': analyze_source_patterns(waste_data),
            'temporal_patterns': analyze_temporal_patterns(waste_data),
            'overproduction_detected': detect_overproduction(waste_data),
            'spoilage_detected': detect_spoilage_issues(waste_data),
            'plate_waste_detected': detect_plate_waste_issues(waste_data),
            'storage_issues_detected': detect_storage_issues(waste_data),
            'preparation_issues_detected': detect_preparation_issues(waste_data),
            'seasonal_patterns_detected': detect_seasonal_patterns(waste_data),
            'efficiency_score': calculate_efficiency_score(waste_data),
            'reduction_opportunities': identify_reduction_opportunities(waste_data)
        }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing waste patterns: {e}")
        return get_empty_patterns()


def calculate_recommendation_priority(
    recommendation: Recommendation,
    patterns: Dict[str, Any]
) -> float:
    """
    Calculate priority score for a recommendation.
    
    Args:
        recommendation: Recommendation object
        patterns: Waste patterns analysis
        
    Returns:
        float: Priority score (0-100)
    """
    try:
        score = 0.0
        
        # Base score from priority level
        priority_scores = {
            Priority.HIGH: 80,
            Priority.MEDIUM: 50,
            Priority.LOW: 20
        }
        score += priority_scores.get(recommendation.priority, 50)
        
        # Impact adjustment
        if recommendation.impact == "high":
            score += 20
        elif recommendation.impact == "medium":
            score += 10
        
        # Potential savings adjustment
        if recommendation.potential_savings > 1000:
            score += 15
        elif recommendation.potential_savings > 500:
            score += 10
        elif recommendation.potential_savings > 100:
            score += 5
        
        # Pattern relevance adjustment
        if recommendation.category in patterns['category_breakdown']:
            category_impact = patterns['category_breakdown'][recommendation.category]['percentage']
            score += category_impact * 0.2
        
        # Implementation effort penalty
        if recommendation.implementation_effort == "high":
            score -= 10
        elif recommendation.implementation_effort == "medium":
            score -= 5
        
        return max(0, min(100, score))
        
    except Exception as e:
        logger.error(f"Error calculating recommendation priority: {e}")
        return 50.0


# Recommendation generation functions

def generate_base_recommendations(
    patterns: Dict[str, Any],
    category_filter: str = None,
    source_filter: str = None
) -> List[Recommendation]:
    """Generate base recommendations from patterns."""
    try:
        recommendations = []
        
        # Category-specific recommendations
        if patterns['category_breakdown']:
            for category, data in patterns['category_breakdown'].items():
                if category_filter and category != category_filter:
                    continue
                
                if data['percentage'] > 30:  # High percentage category
                    recommendations.extend(get_category_specific_recommendations(category, data))
        
        # Source-specific recommendations
        if patterns['source_breakdown']:
            for source, data in patterns['source_breakdown'].items():
                if source_filter and source != source_filter:
                    continue
                
                if data['percentage'] > 25:  # High percentage source
                    recommendations.extend(get_source_specific_recommendations(source, data))
        
        # General recommendations based on patterns
        if patterns['overproduction_detected']:
            recommendations.append(get_overproduction_general_recommendation())
        
        if patterns['spoilage_detected']:
            recommendations.append(get_spoilage_general_recommendation())
        
        if patterns['efficiency_score'] < 50:
            recommendations.append(get_efficiency_improvement_recommendation())
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating base recommendations: {e}")
        return []


def generate_overproduction_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for overproduction issues."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Implement Demand-Based Production",
            description="Reduce overproduction by implementing demand-based meal planning and production scheduling.",
            category="overproduction",
            priority=Priority.HIGH,
            impact="high",
            action_steps=[
                "Analyze historical consumption data to identify demand patterns",
                "Implement just-in-time preparation for high-demand items",
                "Use forecasting models to predict daily demand",
                "Train staff on flexible preparation techniques",
                "Establish buffer stock policies for critical items"
            ],
            potential_savings=patterns.get('overproduction_savings', 500),
            implementation_effort="medium",
            timeline="4-6 weeks",
            success_metrics=[
                "Reduction in overproduction waste by 30%",
                "Improved food freshness",
                "Reduced storage costs"
            ],
            supporting_data={
                "current_overproduction_pct": patterns.get('overproduction_percentage', 0),
                "estimated_savings": patterns.get('overproduction_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating overproduction recommendations: {e}")
        return []


def generate_spoilage_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for spoilage issues."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Optimize Storage and Inventory Management",
            description="Reduce spoilage through better storage conditions, inventory rotation, and shelf-life monitoring.",
            category="spoilage",
            priority=Priority.HIGH,
            impact="high",
            action_steps=[
                "Implement First-In-First-Out (FIFO) inventory system",
                "Review and optimize storage temperatures and conditions",
                "Train staff on proper storage techniques",
                "Implement regular inventory audits",
                "Use digital inventory tracking system"
            ],
            potential_savings=patterns.get('spoilage_savings', 400),
            implementation_effort="medium",
            timeline="3-4 weeks",
            success_metrics=[
                "Reduction in spoilage waste by 40%",
                "Extended shelf life for perishable items",
                "Improved inventory accuracy"
            ],
            supporting_data={
                "current_spoilage_pct": patterns.get('spoilage_percentage', 0),
                "estimated_savings": patterns.get('spoilage_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating spoilage recommendations: {e}")
        return []


def generate_plate_waste_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for plate waste issues."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Implement Portion Control and Student Engagement",
            description="Reduce plate waste through optimized portion sizes and student awareness programs.",
            category="plate_waste",
            priority=Priority.MEDIUM,
            impact="medium",
            action_steps=[
                "Conduct portion size analysis and optimization",
                "Implement trayless dining to reduce waste",
                "Create educational campaigns about food waste",
                "Gather student feedback on meal preferences",
                "Offer smaller portion options"
            ],
            potential_savings=patterns.get('plate_waste_savings', 300),
            implementation_effort="low",
            timeline="2-3 weeks",
            success_metrics=[
                "Reduction in plate waste by 25%",
                "Improved student satisfaction",
                "Reduced food costs"
            ],
            supporting_data={
                "current_plate_waste_pct": patterns.get('plate_waste_percentage', 0),
                "estimated_savings": patterns.get('plate_waste_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating plate waste recommendations: {e}")
        return []


def generate_storage_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for storage issues."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Upgrade Storage Infrastructure and Monitoring",
            description="Improve storage conditions through infrastructure upgrades and real-time monitoring systems.",
            category="storage",
            priority=Priority.MEDIUM,
            impact="medium",
            action_steps=[
                "Install temperature monitoring systems",
                "Upgrade refrigeration units if needed",
                "Implement humidity control systems",
                "Create storage zone optimization plan",
                "Train staff on storage best practices"
            ],
            potential_savings=patterns.get('storage_savings', 250),
            implementation_effort="high",
            timeline="6-8 weeks",
            success_metrics=[
                "Reduced storage-related waste by 20%",
                "Improved food quality and safety",
                "Lower energy costs"
            ],
            supporting_data={
                "storage_issues_pct": patterns.get('storage_issues_percentage', 0),
                "estimated_savings": patterns.get('storage_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating storage recommendations: {e}")
        return []


def generate_preparation_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for preparation issues."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Standardize Preparation Processes and Training",
            description="Reduce preparation waste through standardized processes and enhanced staff training.",
            category="preparation",
            priority=Priority.MEDIUM,
            impact="medium",
            action_steps=[
                "Develop standardized preparation procedures",
                "Conduct staff training on waste reduction techniques",
                "Implement preparation waste tracking",
                "Create waste reduction incentive program",
                "Regularly review and update procedures"
            ],
            potential_savings=patterns.get('preparation_savings', 200),
            implementation_effort="low",
            timeline="3-4 weeks",
            success_metrics=[
                "Reduction in preparation waste by 30%",
                "Improved staff awareness",
                "Consistent food quality"
            ],
            supporting_data={
                "preparation_issues_pct": patterns.get('preparation_issues_percentage', 0),
                "estimated_savings": patterns.get('preparation_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating preparation recommendations: {e}")
        return []


def generate_seasonal_recommendations(patterns: Dict[str, Any]) -> List[Recommendation]:
    """Generate recommendations for seasonal patterns."""
    try:
        recommendations = []
        
        recommendation = Recommendation(
            title="Implement Seasonal Menu Planning",
            description="Optimize menu planning based on seasonal availability and consumption patterns.",
            category="menu_planning",
            priority=Priority.LOW,
            impact="medium",
            action_steps=[
                "Analyze seasonal consumption patterns",
                "Develop seasonal menu cycles",
                "Source seasonal ingredients locally",
                "Adjust procurement based on seasonality",
                "Promote seasonal items to students"
            ],
            potential_savings=patterns.get('seasonal_savings', 150),
            implementation_effort="medium",
            timeline="8-10 weeks",
            success_metrics=[
                "Reduced seasonal waste by 20%",
                "Improved ingredient quality",
                "Lower procurement costs"
            ],
            supporting_data={
                "seasonal_patterns_detected": patterns.get('seasonal_patterns_detected', False),
                "estimated_savings": patterns.get('seasonal_savings', 0)
            }
        )
        
        recommendations.append(recommendation)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating seasonal recommendations: {e}")
        return []


# Helper functions

def get_waste_data(days_back: int) -> pd.DataFrame:
    """Get waste data for analysis."""
    try:
        db = get_session()
        
        start_date = date.today() - timedelta(days=days_back)
        
        records = db.query(WasteRecord).filter(
            WasteRecord.date >= start_date,
            WasteRecord.is_active == True
        ).all()
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'quantity_kg': float(record.quantity_kg),
                'estimated_cost': float(record.estimated_cost or 0),
                'category': record.category,
                'source': record.source,
                'meal_period': record.meal_period,
                'dining_hall': record.dining_hall
            })
        
        df = pd.DataFrame(data)
        db.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting waste data: {e}")
        return pd.DataFrame()


def analyze_category_patterns(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze waste patterns by category."""
    try:
        if waste_data.empty:
            return {}
        
        total_waste = waste_data['quantity_kg'].sum()
        category_stats = waste_data.groupby('category').agg({
            'quantity_kg': ['sum', 'mean', 'count']
        }).round(2)
        
        patterns = {}
        for category in category_stats.index:
            patterns[category] = {
                'total_kg': float(category_stats.loc[category, ('quantity_kg', 'sum')]),
                'avg_kg': float(category_stats.loc[category, ('quantity_kg', 'mean')]),
                'count': int(category_stats.loc[category, ('quantity_kg', 'count')]),
                'percentage': (float(category_stats.loc[category, ('quantity_kg', 'sum')]) / total_waste) * 100
            }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing category patterns: {e}")
        return {}


def analyze_source_patterns(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze waste patterns by source."""
    try:
        if waste_data.empty:
            return {}
        
        total_waste = waste_data['quantity_kg'].sum()
        source_stats = waste_data.groupby('source').agg({
            'quantity_kg': ['sum', 'mean', 'count']
        }).round(2)
        
        patterns = {}
        for source in source_stats.index:
            patterns[source] = {
                'total_kg': float(source_stats.loc[source, ('quantity_kg', 'sum')]),
                'avg_kg': float(source_stats.loc[source, ('quantity_kg', 'mean')]),
                'count': int(source_stats.loc[source, ('quantity_kg', 'count')]),
                'percentage': (float(source_stats.loc[source, ('quantity_kg', 'sum')]) / total_waste) * 100
            }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing source patterns: {e}")
        return {}


def analyze_temporal_patterns(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Analyze temporal waste patterns."""
    try:
        if waste_data.empty:
            return {}
        
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        waste_data['day_of_week'] = waste_data['date'].dt.dayofweek
        waste_data['hour'] = 12  # Default hour
        
        patterns = {
            'peak_day': waste_data.groupby('day_of_week')['quantity_kg'].mean().idxmax(),
            'lowest_day': waste_data.groupby('day_of_week')['quantity_kg'].mean().idxmin(),
            'weekend_vs_weekday': {
                'weekend_avg': waste_data[waste_data['day_of_week'] >= 5]['quantity_kg'].mean(),
                'weekday_avg': waste_data[waste_data['day_of_week'] < 5]['quantity_kg'].mean()
            }
        }
        
        return patterns
        
    except Exception as e:
        logger.error(f"Error analyzing temporal patterns: {e}")
        return {}


def detect_overproduction(waste_data: pd.DataFrame) -> bool:
    """Detect overproduction patterns."""
    try:
        if waste_data.empty:
            return False
        
        # Check if overproduction category is significant
        overproduction_data = waste_data[waste_data['category'] == 'overproduction']
        
        if not overproduction_data.empty:
            overproduction_pct = (overproduction_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            return overproduction_pct > 15  # 15% threshold
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting overproduction: {e}")
        return False


def detect_spoilage_issues(waste_data: pd.DataFrame) -> bool:
    """Detect spoilage issues."""
    try:
        if waste_data.empty:
            return False
        
        spoilage_data = waste_data[waste_data['category'] == 'spoilage']
        
        if not spoilage_data.empty:
            spoilage_pct = (spoilage_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            return spoilage_pct > 10  # 10% threshold
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting spoilage issues: {e}")
        return False


def detect_plate_waste_issues(waste_data: pd.DataFrame) -> bool:
    """Detect plate waste issues."""
    try:
        if waste_data.empty:
            return False
        
        plate_waste_data = waste_data[waste_data['category'] == 'plate_waste']
        
        if not plate_waste_data.empty:
            plate_waste_pct = (plate_waste_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            return plate_waste_pct > 20  # 20% threshold
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting plate waste issues: {e}")
        return False


def detect_storage_issues(waste_data: pd.DataFrame) -> bool:
    """Detect storage issues."""
    try:
        # Check for expired category as proxy for storage issues
        expired_data = waste_data[waste_data['category'] == 'expired']
        
        if not expired_data.empty:
            expired_pct = (expired_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            return expired_pct > 5  # 5% threshold
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting storage issues: {e}")
        return False


def detect_preparation_issues(waste_data: pd.DataFrame) -> bool:
    """Detect preparation issues."""
    try:
        prep_data = waste_data[waste_data['category'] == 'preparation']
        
        if not prep_data.empty:
            prep_pct = (prep_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            return prep_pct > 15  # 15% threshold
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting preparation issues: {e}")
        return False


def detect_seasonal_patterns(waste_data: pd.DataFrame) -> bool:
    """Detect seasonal patterns."""
    try:
        if waste_data.empty or len(waste_data) < 30:
            return False
        
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        waste_data['month'] = waste_data['date'].dt.month
        
        monthly_avg = waste_data.groupby('month')['quantity_kg'].mean()
        
        # Check if there's significant variation between months
        if len(monthly_avg) > 1:
            cv = monthly_avg.std() / monthly_avg.mean()
            return cv > 0.3  # 30% coefficient of variation
        
        return False
        
    except Exception as e:
        logger.error(f"Error detecting seasonal patterns: {e}")
        return False


def calculate_efficiency_score(waste_data: pd.DataFrame) -> float:
    """Calculate efficiency score."""
    try:
        if waste_data.empty:
            return 0.0
        
        # Simple efficiency calculation
        total_waste = waste_data['quantity_kg'].sum()
        avg_daily = total_waste / len(waste_data['date'].unique())
        
        # Score based on daily average (lower is better)
        if avg_daily <= 10:
            return 100.0
        elif avg_daily <= 25:
            return 80.0
        elif avg_daily <= 50:
            return 60.0
        elif avg_daily <= 100:
            return 40.0
        else:
            return max(0, 40 - (avg_daily - 100) * 0.2)
        
    except Exception as e:
        logger.error(f"Error calculating efficiency score: {e}")
        return 0.0


def identify_reduction_opportunities(waste_data: pd.DataFrame) -> List[str]:
    """Identify waste reduction opportunities."""
    try:
        opportunities = []
        
        if waste_data.empty:
            return opportunities
        
        # Analyze top categories
        category_breakdown = analyze_category_patterns(waste_data)
        
        for category, data in category_breakdown.items():
            if data['percentage'] > 20:
                opportunities.append(f"Focus on {category} reduction ({data['percentage']:.1f}% of total waste)")
        
        # Analyze top sources
        source_breakdown = analyze_source_patterns(waste_data)
        
        for source, data in source_breakdown.items():
            if data['percentage'] > 25:
                opportunities.append(f"Address {source} waste ({data['percentage']:.1f}% of total waste)")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error identifying reduction opportunities: {e}")
        return []


def get_empty_patterns() -> Dict[str, Any]:
    """Get empty patterns structure."""
    return {
        'total_waste_kg': 0,
        'total_cost': 0,
        'avg_daily_waste': 0,
        'category_breakdown': {},
        'source_breakdown': {},
        'temporal_patterns': {},
        'overproduction_detected': False,
        'spoilage_detected': False,
        'plate_waste_detected': False,
        'storage_issues_detected': False,
        'preparation_issues_detected': False,
        'seasonal_patterns_detected': False,
        'efficiency_score': 0,
        'reduction_opportunities': []
    }


# Placeholder functions for specific recommendations
def get_category_specific_recommendations(category: str, data: Dict) -> List[Recommendation]:
    """Get category-specific recommendations."""
    return []


def get_source_specific_recommendations(source: str, data: Dict) -> List[Recommendation]:
    """Get source-specific recommendations."""
    return []


def get_overproduction_general_recommendation() -> Recommendation:
    """Get general overproduction recommendation."""
    return Recommendation(
        title="Review Production Planning",
        description="General recommendation to review production planning processes.",
        category="overproduction",
        priority=Priority.MEDIUM,
        impact="medium",
        action_steps=["Review current processes"],
        potential_savings=100,
        implementation_effort="low",
        timeline="2 weeks",
        success_metrics=["Waste reduction"],
        supporting_data={}
    )


def get_spoilage_general_recommendation() -> Recommendation:
    """Get general spoilage recommendation."""
    return Recommendation(
        title="Review Storage Practices",
        description="General recommendation to review storage practices.",
        category="spoilage",
        priority=Priority.MEDIUM,
        impact="medium",
        action_steps=["Review storage practices"],
        potential_savings=100,
        implementation_effort="low",
        timeline="2 weeks",
        success_metrics=["Spoilage reduction"],
        supporting_data={}
    )


def get_efficiency_improvement_recommendation() -> Recommendation:
    """Get efficiency improvement recommendation."""
    return Recommendation(
        title="Improve Overall Efficiency",
        description="General recommendation to improve overall efficiency.",
        category="efficiency",
        priority=Priority.HIGH,
        impact="high",
        action_steps=["Improve processes"],
        potential_savings=200,
        implementation_effort="medium",
        timeline="4 weeks",
        success_metrics=["Efficiency improvement"],
        supporting_data={}
    )
