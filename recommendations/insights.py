"""
Insights generation for GreenPlateAI recommendations.

This module provides functions for generating actionable insights
from waste data analysis and patterns.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import logging

from database.connection import get_session
from models.waste_record import WasteRecord
from utils.helpers import format_currency, format_weight, format_percentage

logger = logging.getLogger(__name__)


def generate_insights(days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Generate comprehensive insights from waste data.
    
    Args:
        days_back: Number of days to analyze
        
    Returns:
        list: Generated insights
    """
    try:
        insights = []
        
        # Get waste data
        waste_data = get_waste_data(days_back)
        
        if waste_data.empty:
            return get_default_insights()
        
        # Generate different types of insights
        insights.extend(get_waste_insights(waste_data))
        insights.extend(get_efficiency_insights(waste_data))
        insights.extend(get_cost_insights(waste_data))
        insights.extend(get_trend_insights(waste_data))
        insights.extend(get_seasonal_insights(waste_data))
        insights.extend(get_operational_insights(waste_data))
        
        # Sort insights by impact and priority
        insights.sort(key=lambda x: (x.get('impact_score', 0), x.get('priority_score', 0)), reverse=True)
        
        logger.info(f"Generated {len(insights)} insights")
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return get_default_insights()


def get_waste_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate waste-specific insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Waste insights
    """
    try:
        insights = []
        
        # Total waste insight
        total_waste = waste_data['quantity_kg'].sum()
        if total_waste > 1000:
            insights.append({
                'type': 'waste_volume',
                'title': 'High Waste Volume Detected',
                'description': f'Total waste of {format_weight(total_waste)} exceeds optimal levels.',
                'impact': 'high',
                'recommendation': 'Implement comprehensive waste reduction program',
                'data_point': total_waste,
                'impact_score': 8,
                'priority_score': 9
            })
        
        # Category breakdown insights
        category_breakdown = waste_data.groupby('category')['quantity_kg'].sum()
        top_category = category_breakdown.idxmax()
        top_category_pct = (category_breakdown.max() / category_breakdown.sum()) * 100
        
        if top_category_pct > 40:
            insights.append({
                'type': 'category_focus',
                'title': f'{top_category.title()} Waste Dominates',
                'description': f'{top_category.title()} accounts for {format_percentage(top_category_pct)} of total waste.',
                'impact': 'high',
                'recommendation': f'Focus reduction efforts on {top_category} category',
                'data_point': top_category_pct,
                'impact_score': 7,
                'priority_score': 8
            })
        
        # Plate waste insight
        plate_waste_data = waste_data[waste_data['category'] == 'plate_waste']
        if not plate_waste_data.empty:
            plate_waste_pct = (plate_waste_data['quantity_kg'].sum() / waste_data['quantity_kg'].sum()) * 100
            if plate_waste_pct > 25:
                insights.append({
                    'type': 'plate_waste',
                    'title': 'High Plate Waste Levels',
                    'description': f'Plate waste represents {format_percentage(plate_waste_pct)} of total waste.',
                    'impact': 'medium',
                    'recommendation': 'Implement portion control and student education programs',
                    'data_point': plate_waste_pct,
                    'impact_score': 6,
                    'priority_score': 7
                })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating waste insights: {e}")
        return []


def get_efficiency_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate efficiency-related insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Efficiency insights
    """
    try:
        insights = []
        
        # Daily average insight
        daily_avg = waste_data.groupby('date')['quantity_kg'].sum().mean()
        if daily_avg > 50:
            insights.append({
                'type': 'efficiency',
                'title': 'High Daily Waste Average',
                'description': f'Daily waste average of {format_weight(daily_avg)} indicates efficiency issues.',
                'impact': 'high',
                'recommendation': 'Review production planning and inventory management',
                'data_point': daily_avg,
                'impact_score': 7,
                'priority_score': 8
            })
        
        # Consistency insight
        daily_std = waste_data.groupby('date')['quantity_kg'].sum().std()
        daily_mean = waste_data.groupby('date')['quantity_kg'].sum().mean()
        
        if daily_mean > 0:
            cv = daily_std / daily_mean  # Coefficient of variation
            if cv > 0.5:
                insights.append({
                    'type': 'consistency',
                    'title': 'Inconsistent Waste Patterns',
                    'description': f'High variability in daily waste (CV: {cv:.2f}) suggests inconsistent operations.',
                    'impact': 'medium',
                    'recommendation': 'Standardize processes and improve forecasting',
                    'data_point': cv,
                    'impact_score': 6,
                    'priority_score': 7
                })
        
        # Peak day insight
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        waste_data['day_of_week'] = waste_data['date'].dt.dayofweek
        dow_avg = waste_data.groupby('day_of_week')['quantity_kg'].sum()
        
        if len(dow_avg) > 0:
            peak_day = dow_avg.idxmax()
            peak_day_waste = dow_avg.max()
            avg_day_waste = dow_avg.mean()
            
            if peak_day_waste > avg_day_waste * 1.5:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                insights.append({
                    'type': 'peak_day',
                    'title': f'{day_names[peak_day]} Peak Waste',
                    'description': f'{day_names[peak_day]} shows {format_percentage((peak_day_waste/avg_day_waste - 1) * 100)} higher waste than average.',
                    'impact': 'medium',
                    'recommendation': 'Investigate and address {day_names[peak_day]} specific issues',
                    'data_point': peak_day_waste,
                    'impact_score': 5,
                    'priority_score': 6
                })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating efficiency insights: {e}")
        return []


def get_cost_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate cost-related insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Cost insights
    """
    try:
        insights = []
        
        # Total cost insight
        total_cost = waste_data['estimated_cost'].sum()
        if total_cost > 5000:
            insights.append({
                'type': 'cost_impact',
                'title': 'High Financial Impact',
                'description': f'Total waste cost of {format_currency(total_cost)} represents significant financial loss.',
                'impact': 'high',
                'recommendation': 'Prioritize cost reduction initiatives',
                'data_point': total_cost,
                'impact_score': 9,
                'priority_score': 9
            })
        
        # Cost per kg insight
        total_waste = waste_data['quantity_kg'].sum()
        if total_waste > 0:
            cost_per_kg = total_cost / total_waste
            if cost_per_kg > 10:
                insights.append({
                    'type': 'cost_efficiency',
                    'title': 'High Cost per Kilogram',
                    'description': f'Average cost of {format_currency(cost_per_kg)}/kg indicates expensive items being wasted.',
                    'impact': 'high',
                    'recommendation': 'Focus on reducing waste of high-cost items',
                    'data_point': cost_per_kg,
                    'impact_score': 7,
                    'priority_score': 8
                })
        
        # Category cost insight
        category_cost = waste_data.groupby('category')['estimated_cost'].sum()
        if not category_cost.empty:
            highest_cost_category = category_cost.idxmax()
            highest_cost_pct = (category_cost.max() / category_cost.sum()) * 100
            
            if highest_cost_pct > 35:
                insights.append({
                    'type': 'category_cost',
                    'title': f'{highest_cost_category.title()} Cost Impact',
                    'description': f'{highest_cost_category.title()} accounts for {format_percentage(highest_cost_pct)} of total waste cost.',
                    'impact': 'high',
                    'recommendation': f'Target {highest_cost_category} for immediate cost reduction',
                    'data_point': highest_cost_pct,
                    'impact_score': 8,
                    'priority_score': 9
                })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating cost insights: {e}")
        return []


def get_trend_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate trend-related insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Trend insights
    """
    try:
        insights = []
        
        if len(waste_data) < 7:
            return insights
        
        # Calculate trend
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        daily_waste = waste_data.groupby('date')['quantity_kg'].sum().sort_index()
        
        # Simple linear regression for trend
        x = np.arange(len(daily_waste))
        y = daily_waste.values
        
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]
            avg_value = daily_waste.mean()
            
            if avg_value > 0:
                trend_percentage = (slope * len(daily_waste) / avg_value) * 100
                
                if trend_percentage > 20:
                    insights.append({
                        'type': 'trend',
                        'title': 'Increasing Waste Trend',
                        'description': f'Waste is increasing by {format_percentage(trend_percentage)} over the analyzed period.',
                        'impact': 'high',
                        'recommendation': 'Implement immediate intervention measures',
                        'data_point': trend_percentage,
                        'impact_score': 8,
                        'priority_score': 9
                    })
                elif trend_percentage < -20:
                    insights.append({
                        'type': 'trend',
                        'title': 'Positive Waste Reduction Trend',
                        'description': f'Waste is decreasing by {format_percentage(abs(trend_percentage))} - continue current strategies.',
                        'impact': 'positive',
                        'recommendation': 'Maintain and expand successful practices',
                        'data_point': trend_percentage,
                        'impact_score': 6,
                        'priority_score': 3
                    })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating trend insights: {e}")
        return []


def get_seasonal_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate seasonal insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Seasonal insights
    """
    try:
        insights = []
        
        if len(waste_data) < 30:
            return insights
        
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        waste_data['month'] = waste_data['date'].dt.month
        
        monthly_avg = waste_data.groupby('month')['quantity_kg'].mean()
        
        if len(monthly_avg) > 1:
            # Check for seasonal variation
            cv = monthly_avg.std() / monthly_avg.mean()
            
            if cv > 0.3:
                insights.append({
                    'type': 'seasonal',
                    'title': 'Significant Seasonal Variation',
                    'description': f'Seasonal variation (CV: {cv:.2f}) indicates seasonal patterns in waste.',
                    'impact': 'medium',
                    'recommendation': 'Implement seasonal planning and adjustment strategies',
                    'data_point': cv,
                    'impact_score': 6,
                    'priority_score': 7
                })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating seasonal insights: {e}")
        return []


def get_operational_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generate operational insights.
    
    Args:
        waste_data: Waste data DataFrame
        
    Returns:
        list: Operational insights
    """
    try:
        insights = []
        
        # Meal period insights
        if 'meal_period' in waste_data.columns:
            meal_period_waste = waste_data.groupby('meal_period')['quantity_kg'].sum()
            
            if len(meal_period_waste) > 0:
                highest_meal_period = meal_period_waste.idxmax()
                if highest_meal_period:
                    insights.append({
                        'type': 'operational',
                        'title': f'{highest_meal_period.title()} Peak Waste',
                        'description': f'{highest_meal_period.title()} generates the most waste - review planning and preparation.',
                        'impact': 'medium',
                        'recommendation': f'Optimize {highest_meal_period} operations and planning',
                        'data_point': highest_meal_period,
                        'impact_score': 5,
                        'priority_score': 6
                    })
        
        # Dining hall insights
        if 'dining_hall' in waste_data.columns:
            hall_waste = waste_data.groupby('dining_hall')['quantity_kg'].sum()
            
            if len(hall_waste) > 0:
                worst_hall = hall_waste.idxmax()
                if worst_hall:
                    insights.append({
                        'type': 'operational',
                        'title': f'{worst_hall} Performance Issue',
                        'description': f'{worst_hall} shows highest waste levels - requires attention.',
                        'impact': 'medium',
                        'recommendation': f'Conduct detailed analysis of {worst_hall} operations',
                        'data_point': worst_hall,
                        'impact_score': 6,
                        'priority_score': 7
                    })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating operational insights: {e}")
        return []


def get_waste_data(days_back: int) -> pd.DataFrame:
    """Get waste data for insights analysis."""
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


def get_default_insights() -> List[Dict[str, Any]]:
    """Get default insights when no data is available."""
    return [
        {
            'type': 'data_availability',
            'title': 'Insufficient Data Available',
            'description': 'Not enough historical data to generate meaningful insights.',
            'impact': 'low',
            'recommendation': 'Continue collecting waste data to enable better analysis',
            'data_point': 0,
            'impact_score': 2,
            'priority_score': 3
        },
        {
            'type': 'data_collection',
            'title': 'Start Data Collection',
            'description': 'Begin systematic waste tracking to identify improvement opportunities.',
            'impact': 'medium',
            'recommendation': 'Implement waste tracking system and establish baseline metrics',
            'data_point': 0,
            'impact_score': 5,
            'priority_score': 6
        }
    ]


def calculate_insight_priority(insight: Dict[str, Any]) -> int:
    """
    Calculate priority score for an insight.
    
    Args:
        insight: Insight dictionary
        
    Returns:
        int: Priority score (1-10)
    """
    try:
        base_score = 5
        
        # Adjust based on impact
        impact_multipliers = {
            'high': 1.5,
            'medium': 1.0,
            'low': 0.5,
            'positive': 0.3
        }
        
        impact = insight.get('impact', 'medium')
        multiplier = impact_multipliers.get(impact, 1.0)
        
        final_score = int(base_score * multiplier)
        return max(1, min(10, final_score))
        
    except Exception as e:
        logger.error(f"Error calculating insight priority: {e}")
        return 5


def format_insight_message(insight: Dict[str, Any]) -> str:
    """
    Format insight message for display.
    
    Args:
        insight: Insight dictionary
        
    Returns:
        str: Formatted message
    """
    try:
        message = f"**{insight.get('title', 'Insight')}**\n\n"
        message += f"{insight.get('description', 'No description available')}\n\n"
        message += f"**Recommendation:** {insight.get('recommendation', 'No recommendation available')}"
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting insight message: {e}")
        return "Error formatting insight"


def get_insight_summary(insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for insights.
    
    Args:
        insights: List of insights
        
    Returns:
        dict: Summary statistics
    """
    try:
        if not insights:
            return {
                'total_insights': 0,
                'high_impact': 0,
                'medium_impact': 0,
                'low_impact': 0,
                'average_priority': 0
            }
        
        impact_counts = {'high': 0, 'medium': 0, 'low': 0, 'positive': 0}
        total_priority = 0
        
        for insight in insights:
            impact = insight.get('impact', 'medium')
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
            total_priority += insight.get('priority_score', 5)
        
        summary = {
            'total_insights': len(insights),
            'high_impact': impact_counts['high'],
            'medium_impact': impact_counts['medium'],
            'low_impact': impact_counts['low'],
            'positive_insights': impact_counts['positive'],
            'average_priority': total_priority / len(insights),
            'top_insights': insights[:3]  # Top 3 insights
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating insight summary: {e}")
        return {'error': str(e)}
