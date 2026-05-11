"""
Data aggregation utilities for GreenPlateAI analytics dashboard.

This module provides comprehensive data aggregation and calculation
functions for dashboard metrics and KPIs.
"""

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path

from database.connection import get_session
from database.models import FoodWasteLog, MealLog, User, SustainabilityMetric, MealType, WasteCategory

logger = logging.getLogger(__name__)


class AnalyticsDataAggregator:
    """Data aggregation for analytics dashboard."""
    
    def __init__(self):
        """Initialize the data aggregator."""
        self.session = get_session()
        self.data_cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)
    
    def get_dashboard_data(self, start_date: date = None, end_date: date = None,
                          dining_hall: str = None) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        cache_key = f"dashboard_{start_date}_{end_date}_{dining_hall}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.info("Using cached dashboard data")
            return self.data_cache[cache_key]
        
        logger.info("Aggregating dashboard data")
        
        # Set default date range
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=30)  # Last 30 days by default
        
        # Get data from database
        meal_data = self._get_meal_data(start_date, end_date, dining_hall)
        waste_data = self._get_waste_data(start_date, end_date, dining_hall)
        user_data = self._get_user_data(start_date, end_date)
        sustainability_data = self._get_sustainability_data(start_date, end_date, dining_hall)
        
        # Calculate metrics
        dashboard_data = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days + 1
            },
            'filters': {
                'dining_hall': dining_hall
            },
            'kpi_metrics': self._calculate_kpi_metrics(meal_data, waste_data, sustainability_data),
            'meal_popularity': self._calculate_meal_popularity(meal_data),
            'student_satisfaction': self._calculate_student_satisfaction(meal_data),
            'environmental_impact': self._calculate_environmental_impact(waste_data, sustainability_data),
            'financial_metrics': self._calculate_financial_metrics(meal_data, waste_data),
            'trends': self._calculate_trends(meal_data, waste_data, start_date, end_date),
            'dining_hall_comparison': self._calculate_dining_hall_comparison(meal_data, waste_data),
            'category_analysis': self._calculate_category_analysis(waste_data),
            'time_patterns': self._calculate_time_patterns(meal_data, waste_data)
        }
        
        # Cache the result
        self.data_cache[cache_key] = dashboard_data
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        logger.info(f"Dashboard data aggregated for {len(meal_data)} meals and {len(waste_data)} waste records")
        
        return dashboard_data
    
    def _get_meal_data(self, start_date: date, end_date: date, dining_hall: str = None) -> pd.DataFrame:
        """Get meal data from database."""
        query = self.session.query(MealLog).filter(
            MealLog.meal_date >= start_date,
            MealLog.meal_date <= end_date,
            MealLog.is_active == True
        )
        
        if dining_hall:
            query = query.filter(MealLog.dining_hall == dining_hall)
        
        meal_logs = query.all()
        
        data = []
        for log in meal_logs:
            data.append({
                'date': log.meal_date,
                'meal_type': log.meal_type.value,
                'dining_hall': log.dining_hall,
                'calories': log.calories or 0,
                'protein': log.protein or 0,
                'carbs': log.carbs or 0,
                'fat': log.fat or 0,
                'fiber': log.fiber or 0,
                'satisfaction_rating': log.satisfaction_rating or 0,
                'portion_size_rating': log.portion_size_rating or 0,
                'taste_rating': log.taste_rating or 0,
                'meal_items': log.meal_items or {},
                'user_id': log.user_id,
                'meal_time': log.meal_time
            })
        
        return pd.DataFrame(data)
    
    def _get_waste_data(self, start_date: date, end_date: date, dining_hall: str = None) -> pd.DataFrame:
        """Get waste data from database."""
        query = self.session.query(FoodWasteLog).filter(
            FoodWasteLog.waste_date >= start_date,
            FoodWasteLog.waste_date <= end_date,
            FoodWasteLog.is_active == True
        )
        
        if dining_hall:
            query = query.filter(FoodWasteLog.dining_hall == dining_hall)
        
        waste_logs = query.all()
        
        data = []
        for log in waste_logs:
            data.append({
                'date': log.waste_date,
                'meal_type': log.meal_period.value if log.meal_period else 'unknown',
                'dining_hall': log.dining_hall,
                'food_item': log.food_item,
                'category': log.category,
                'waste_category': log.waste_category.value,
                'quantity': log.quantity_kg,
                'estimated_cost': log.estimated_cost or 0,
                'reason': log.reason or '',
                'temperature': log.temperature or 0,
                'co2_equivalent': log.co2_equivalent_kg or 0,
                'water_footprint': log.water_footprint_liters or 0,
                'land_use': log.land_use_m2 or 0,
                'food_quality_rating': log.food_quality_rating or 0,
                'appearance_rating': log.appearance_rating or 0,
                'recorded_by': log.recorded_by or '',
                'waste_time': log.waste_time
            })
        
        return pd.DataFrame(data)
    
    def _get_user_data(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get user data from database."""
        users = self.session.query(User).filter(
            User.is_active == True
        ).all()
        
        data = []
        for user in users:
            data.append({
                'user_id': user.id,
                'full_name': user.full_name,
                'email': user.email,
                'role': user.role.value,
                'dining_hall_preference': user.dining_hall_preference,
                'created_at': user.created_at,
                'last_login': user.last_login
            })
        
        return pd.DataFrame(data)
    
    def _get_sustainability_data(self, start_date: date, end_date: date, dining_hall: str = None) -> pd.DataFrame:
        """Get sustainability data from database."""
        query = self.session.query(SustainabilityMetric).filter(
            SustainabilityMetric.metric_date >= start_date,
            SustainabilityMetric.metric_date <= end_date,
            SustainabilityMetric.is_active == True
        )
        
        if dining_hall:
            query = query.filter(SustainabilityMetric.dining_hall == dining_hall)
        
        metrics = query.all()
        
        data = []
        for metric in metrics:
            data.append({
                'date': metric.metric_date,
                'dining_hall': metric.dining_hall,
                'co2_saved_kg': metric.co2_saved_kg or 0,
                'water_saved_liters': metric.water_saved_liters or 0,
                'waste_reduced_kg': metric.waste_reduced_kg or 0,
                'cost_saved': metric.cost_saved or 0,
                'meals_served': metric.meals_served or 0,
                'satisfaction_score': metric.satisfaction_score or 0
            })
        
        return pd.DataFrame(data)
    
    def _calculate_kpi_metrics(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame,
                             sustainability_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate KPI metrics for dashboard."""
        kpis = {}
        
        # Total food waste
        if not waste_data.empty:
            total_waste = waste_data['quantity'].sum()
            kpis['total_food_waste'] = {
                'value': total_waste,
                'unit': 'kg',
                'change': self._calculate_change(waste_data, 'quantity'),
                'trend': self._get_trend_direction(waste_data, 'quantity')
            }
        else:
            kpis['total_food_waste'] = {'value': 0, 'unit': 'kg', 'change': 0, 'trend': 'stable'}
        
        # Total meals served
        if not meal_data.empty:
            total_meals = len(meal_data)
            kpis['total_meals_served'] = {
                'value': total_meals,
                'unit': 'meals',
                'change': self._calculate_change(meal_data, 'user_id'),
                'trend': self._get_trend_direction(meal_data, 'user_id')
            }
        else:
            kpis['total_meals_served'] = {'value': 0, 'unit': 'meals', 'change': 0, 'trend': 'stable'}
        
        # Average satisfaction
        if not meal_data.empty:
            avg_satisfaction = meal_data['satisfaction_rating'].mean()
            kpis['avg_satisfaction'] = {
                'value': avg_satisfaction,
                'unit': 'score',
                'change': self._calculate_change(meal_data, 'satisfaction_rating'),
                'trend': self._get_trend_direction(meal_data, 'satisfaction_rating')
            }
        else:
            kpis['avg_satisfaction'] = {'value': 0, 'unit': 'score', 'change': 0, 'trend': 'stable'}
        
        # CO₂ reduction
        if not sustainability_data.empty:
            co2_reduction = sustainability_data['co2_saved_kg'].sum()
            kpis['co2_reduction'] = {
                'value': co2_reduction,
                'unit': 'kg',
                'change': self._calculate_change(sustainability_data, 'co2_saved_kg'),
                'trend': self._get_trend_direction(sustainability_data, 'co2_saved_kg')
            }
        else:
            # Calculate from waste data if sustainability data not available
            if not waste_data.empty:
                co2_reduction = waste_data['co2_equivalent'].sum()
                kpis['co2_reduction'] = {
                    'value': co2_reduction,
                    'unit': 'kg',
                    'change': self._calculate_change(waste_data, 'co2_equivalent'),
                    'trend': self._get_trend_direction(waste_data, 'co2_equivalent')
                }
            else:
                kpis['co2_reduction'] = {'value': 0, 'unit': 'kg', 'change': 0, 'trend': 'stable'}
        
        # Financial savings
        if not sustainability_data.empty:
            financial_savings = sustainability_data['cost_saved'].sum()
            kpis['financial_savings'] = {
                'value': financial_savings,
                'unit': '$',
                'change': self._calculate_change(sustainability_data, 'cost_saved'),
                'trend': self._get_trend_direction(sustainability_data, 'cost_saved')
            }
        else:
            # Calculate from waste data if sustainability data not available
            if not waste_data.empty:
                financial_savings = waste_data['estimated_cost'].sum()
                kpis['financial_savings'] = {
                    'value': financial_savings,
                    'unit': '$',
                    'change': self._calculate_change(waste_data, 'estimated_cost'),
                    'trend': self._get_trend_direction(waste_data, 'estimated_cost')
                }
            else:
                kpis['financial_savings'] = {'value': 0, 'unit': '$', 'change': 0, 'trend': 'stable'}
        
        # Waste percentage
        if not meal_data.empty and not waste_data.empty:
            waste_percentage = (waste_data['quantity'].sum() / len(meal_data)) * 100
            kpis['waste_percentage'] = {
                'value': waste_percentage,
                'unit': '%',
                'change': 0,  # Would need historical data for comparison
                'trend': 'stable'
            }
        else:
            kpis['waste_percentage'] = {'value': 0, 'unit': '%', 'change': 0, 'trend': 'stable'}
        
        return kpis
    
    def _calculate_meal_popularity(self, meal_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate meal popularity metrics."""
        if meal_data.empty:
            return {'by_meal_type': {}, 'by_dining_hall': {}, 'top_items': {}}
        
        popularity = {}
        
        # By meal type
        meal_type_counts = meal_data['meal_type'].value_counts()
        popularity['by_meal_type'] = meal_type_counts.to_dict()
        
        # By dining hall
        dining_hall_counts = meal_data['dining_hall'].value_counts()
        popularity['by_dining_hall'] = dining_hall_counts.to_dict()
        
        # Top meal items
        all_items = []
        for _, row in meal_data.iterrows():
            if isinstance(row['meal_items'], dict):
                all_items.extend(row['meal_items'].keys())
        
        if all_items:
            item_counts = pd.Series(all_items).value_counts().head(10)
            popularity['top_items'] = item_counts.to_dict()
        else:
            popularity['top_items'] = {}
        
        return popularity
    
    def _calculate_student_satisfaction(self, meal_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate student satisfaction metrics."""
        if meal_data.empty:
            return {'overall': 0, 'by_meal_type': {}, 'by_dining_hall': {}, 'trends': {}}
        
        satisfaction = {}
        
        # Overall satisfaction
        satisfaction['overall'] = meal_data['satisfaction_rating'].mean()
        
        # By meal type
        meal_type_satisfaction = meal_data.groupby('meal_type')['satisfaction_rating'].mean()
        satisfaction['by_meal_type'] = meal_type_satisfaction.to_dict()
        
        # By dining hall
        dining_hall_satisfaction = meal_data.groupby('dining_hall')['satisfaction_rating'].mean()
        satisfaction['by_dining_hall'] = dining_hall_satisfaction.to_dict()
        
        # Satisfaction trends
        if 'date' in meal_data.columns:
            daily_satisfaction = meal_data.groupby('date')['satisfaction_rating'].mean()
            satisfaction['trends'] = daily_satisfaction.to_dict()
        else:
            satisfaction['trends'] = {}
        
        # Rating distribution
        rating_counts = meal_data['satisfaction_rating'].value_counts().sort_index()
        satisfaction['rating_distribution'] = rating_counts.to_dict()
        
        return satisfaction
    
    def _calculate_environmental_impact(self, waste_data: pd.DataFrame,
                                      sustainability_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate environmental impact metrics."""
        impact = {}
        
        # From waste data
        if not waste_data.empty:
            impact['from_waste'] = {
                'co2_equivalent': waste_data['co2_equivalent'].sum(),
                'water_footprint': waste_data['water_footprint'].sum(),
                'land_use': waste_data['land_use'].sum()
            }
        else:
            impact['from_waste'] = {'co2_equivalent': 0, 'water_footprint': 0, 'land_use': 0}
        
        # From sustainability data
        if not sustainability_data.empty:
            impact['from_sustainability'] = {
                'co2_saved': sustainability_data['co2_saved_kg'].sum(),
                'water_saved': sustainability_data['water_saved_liters'].sum(),
                'waste_reduced': sustainability_data['waste_reduced_kg'].sum()
            }
        else:
            impact['from_sustainability'] = {'co2_saved': 0, 'water_saved': 0, 'waste_reduced': 0}
        
        # Net impact
        impact['net'] = {
            'co2_impact': impact['from_sustainability']['co2_saved'] - impact['from_waste']['co2_equivalent'],
            'water_impact': impact['from_sustainability']['water_saved'] - impact['from_waste']['water_footprint'],
            'waste_reduction': impact['from_sustainability']['waste_reduced']
        }
        
        return impact
    
    def _calculate_financial_metrics(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate financial metrics."""
        financial = {}
        
        # Cost from waste
        if not waste_data.empty:
            waste_cost = waste_data['estimated_cost'].sum()
            financial['waste_cost'] = waste_cost
        else:
            financial['waste_cost'] = 0
        
        # Cost savings from sustainability
        # Note: This would need actual cost data - using estimates
        financial['estimated_savings'] = financial['waste_cost'] * 0.8  # Assume 80% could be saved
        
        # Cost per meal
        if not meal_data.empty and not waste_data.empty:
            cost_per_meal = financial['waste_cost'] / len(meal_data)
            financial['cost_per_meal'] = cost_per_meal
        else:
            financial['cost_per_meal'] = 0
        
        # Financial trends
        if not waste_data.empty and 'date' in waste_data.columns:
            daily_cost = waste_data.groupby('date')['estimated_cost'].sum()
            financial['daily_trends'] = daily_cost.to_dict()
        else:
            financial['daily_trends'] = {}
        
        return financial
    
    def _calculate_trends(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame,
                         start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate weekly and monthly trends."""
        trends = {}
        
        # Weekly trends
        trends['weekly'] = self._calculate_weekly_trends(meal_data, waste_data, start_date, end_date)
        
        # Monthly trends
        trends['monthly'] = self._calculate_monthly_trends(meal_data, waste_data, start_date, end_date)
        
        return trends
    
    def _calculate_weekly_trends(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame,
                                start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate weekly trends."""
        weekly = {}
        
        # Meal trends
        if not meal_data.empty and 'date' in meal_data.columns:
            meal_data['week'] = pd.to_datetime(meal_data['date']).dt.isocalendar().week
            weekly_meals = meal_data.groupby('week').agg({
                'user_id': 'count',
                'satisfaction_rating': 'mean',
                'calories': 'sum',
                'protein': 'sum'
            })
            weekly['meals'] = weekly_meals.to_dict('index')
        else:
            weekly['meals'] = {}
        
        # Waste trends
        if not waste_data.empty and 'date' in waste_data.columns:
            waste_data['week'] = pd.to_datetime(waste_data['date']).dt.isocalendar().week
            weekly_waste = waste_data.groupby('week').agg({
                'quantity': 'sum',
                'estimated_cost': 'sum',
                'co2_equivalent': 'sum'
            })
            weekly['waste'] = weekly_waste.to_dict('index')
        else:
            weekly['waste'] = {}
        
        return weekly
    
    def _calculate_monthly_trends(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame,
                                 start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate monthly trends."""
        monthly = {}
        
        # Meal trends
        if not meal_data.empty and 'date' in meal_data.columns:
            meal_data['month'] = pd.to_datetime(meal_data['date']).dt.month
            monthly_meals = meal_data.groupby('month').agg({
                'user_id': 'count',
                'satisfaction_rating': 'mean',
                'calories': 'sum',
                'protein': 'sum'
            })
            monthly['meals'] = monthly_meals.to_dict('index')
        else:
            monthly['meals'] = {}
        
        # Waste trends
        if not waste_data.empty and 'date' in waste_data.columns:
            waste_data['month'] = pd.to_datetime(waste_data['date']).dt.month
            monthly_waste = waste_data.groupby('month').agg({
                'quantity': 'sum',
                'estimated_cost': 'sum',
                'co2_equivalent': 'sum'
            })
            monthly['waste'] = monthly_waste.to_dict('index')
        else:
            monthly['waste'] = {}
        
        return monthly
    
    def _calculate_dining_hall_comparison(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate dining hall comparison metrics."""
        comparison = {}
        
        # Meal comparison
        if not meal_data.empty:
            hall_meals = meal_data.groupby('dining_hall').agg({
                'user_id': 'count',
                'satisfaction_rating': 'mean',
                'calories': 'mean',
                'protein': 'mean'
            })
            comparison['meals'] = hall_meals.to_dict('index')
        else:
            comparison['meals'] = {}
        
        # Waste comparison
        if not waste_data.empty:
            hall_waste = waste_data.groupby('dining_hall').agg({
                'quantity': 'sum',
                'estimated_cost': 'sum',
                'co2_equivalent': 'sum'
            })
            comparison['waste'] = hall_waste.to_dict('index')
        else:
            comparison['waste'] = {}
        
        return comparison
    
    def _calculate_category_analysis(self, waste_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate waste category analysis."""
        if waste_data.empty:
            return {'by_category': {}, 'by_waste_type': {}, 'top_items': {}}
        
        analysis = {}
        
        # By food category
        category_waste = waste_data.groupby('category').agg({
            'quantity': 'sum',
            'estimated_cost': 'sum',
            'co2_equivalent': 'sum'
        })
        analysis['by_category'] = category_waste.to_dict('index')
        
        # By waste type
        waste_type_waste = waste_data.groupby('waste_category').agg({
            'quantity': 'sum',
            'estimated_cost': 'sum',
            'co2_equivalent': 'sum'
        })
        analysis['by_waste_type'] = waste_type_waste.to_dict('index')
        
        # Top waste items
        item_waste = waste_data.groupby('food_item').agg({
            'quantity': 'sum',
            'estimated_cost': 'sum'
        }).sort_values('quantity', ascending=False).head(10)
        analysis['top_items'] = item_waste.to_dict('index')
        
        return analysis
    
    def _calculate_time_patterns(self, meal_data: pd.DataFrame, waste_data: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time-based patterns."""
        patterns = {}
        
        # Day of week patterns
        if not meal_data.empty and 'date' in meal_data.columns:
            meal_data['day_of_week'] = pd.to_datetime(meal_data['date']).dt.day_name()
            dow_meals = meal_data.groupby('day_of_week').agg({
                'user_id': 'count',
                'satisfaction_rating': 'mean'
            })
            patterns['day_of_week_meals'] = dow_meals.to_dict('index')
        else:
            patterns['day_of_week_meals'] = {}
        
        if not waste_data.empty and 'date' in waste_data.columns:
            waste_data['day_of_week'] = pd.to_datetime(waste_data['date']).dt.day_name()
            dow_waste = waste_data.groupby('day_of_week').agg({
                'quantity': 'sum',
                'estimated_cost': 'sum'
            })
            patterns['day_of_week_waste'] = dow_waste.to_dict('index')
        else:
            patterns['day_of_week_waste'] = {}
        
        # Hourly patterns (if time data available)
        if not meal_data.empty and 'meal_time' in meal_data.columns:
            meal_data['hour'] = pd.to_datetime(meal_data['meal_time']).dt.hour
            hourly_meals = meal_data.groupby('hour')['user_id'].count()
            patterns['hourly_meals'] = hourly_meals.to_dict()
        else:
            patterns['hourly_meals'] = {}
        
        return patterns
    
    def _calculate_change(self, data: pd.DataFrame, column: str) -> float:
        """Calculate percentage change."""
        if data.empty or column not in data.columns:
            return 0.0
        
        # Sort by date if available
        if 'date' in data.columns:
            data = data.sort_values('date')
        
        # Split data into two halves
        mid_point = len(data) // 2
        if mid_point == 0:
            return 0.0
        
        first_half = data.iloc[:mid_point][column]
        second_half = data.iloc[mid_point:][column]
        
        first_avg = first_half.mean()
        second_avg = second_half.mean()
        
        if first_avg == 0:
            return 0.0
        
        change = ((second_avg - first_avg) / first_avg) * 100
        return round(change, 1)
    
    def _get_trend_direction(self, data: pd.DataFrame, column: str) -> str:
        """Get trend direction."""
        change = self._calculate_change(data, column)
        
        if change > 5:
            return 'increasing'
        elif change < -5:
            return 'decreasing'
        else:
            return 'stable'
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid."""
        if cache_key not in self.data_cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        self.cache_expiry.clear()
        logger.info("Cache cleared")
    
    def export_summary(self, data: Dict[str, Any], format: str = 'json') -> str:
        """Export dashboard summary."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'json':
            import json
            filename = f"dashboard_summary_{timestamp}.json"
            filepath = Path("exports")
            filepath.mkdir(parents=True, exist_ok=True)
            filepath = filepath / filename
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return str(filepath)
        
        elif format.lower() == 'csv':
            # Convert to CSV for key metrics
            filename = f"dashboard_summary_{timestamp}.csv"
            filepath = Path("exports")
            filepath.mkdir(parents=True, exist_ok=True)
            filepath = filepath / filename
            
            # Create summary DataFrame
            summary_data = []
            
            # KPIs
            for kpi, values in data.get('kpi_metrics', {}).items():
                summary_data.append({
                    'Metric': kpi,
                    'Value': values.get('value', 0),
                    'Unit': values.get('unit', ''),
                    'Change': values.get('change', 0),
                    'Trend': values.get('trend', '')
                })
            
            df = pd.DataFrame(summary_data)
            df.to_csv(filepath, index=False)
            
            return str(filepath)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# Convenience functions for direct use
def get_dashboard_data(start_date: date = None, end_date: date = None, dining_hall: str = None) -> Dict[str, Any]:
    """Get dashboard data."""
    aggregator = AnalyticsDataAggregator()
    return aggregator.get_dashboard_data(start_date, end_date, dining_hall)


def export_dashboard_summary(data: Dict[str, Any], format: str = 'json') -> str:
    """Export dashboard summary."""
    aggregator = AnalyticsDataAggregator()
    return aggregator.export_summary(data, format)
