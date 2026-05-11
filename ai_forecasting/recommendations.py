"""
Recommendation generation system for AI forecasting.

This module provides intelligent recommendations for demand
and waste reduction based on AI predictions.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from .predictions import DemandPredictor, WastePredictor
from .data_preprocessing import DataPreprocessor

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """AI-powered recommendation engine for food service operations."""
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.demand_predictor = DemandPredictor()
        self.waste_predictor = WastePredictor()
        self.preprocessor = DataPreprocessor()
    
    def generate_daily_recommendations(self, forecast_date: date, dining_hall: str) -> Dict[str, Any]:
        """Generate comprehensive daily recommendations."""
        logger.info(f"Generating daily recommendations for {forecast_date} at {dining_hall}")
        
        recommendations = {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'demand_recommendations': [],
            'waste_recommendations': [],
            'operational_recommendations': [],
            'cost_savings': {},
            'priority_actions': []
        }
        
        # Get predictions for all meal types
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            try:
                # Demand prediction
                demand_pred = self.demand_predictor.predict_meal_demand(forecast_date, dining_hall, meal_type)
                
                # Waste prediction
                waste_pred = self.waste_predictor.predict_waste_by_category(forecast_date, dining_hall, meal_type)
                
                # Generate meal-specific recommendations
                meal_recs = self._generate_meal_recommendations(demand_pred, waste_pred, meal_type)
                recommendations['demand_recommendations'].extend(meal_recs['demand'])
                recommendations['waste_recommendations'].extend(meal_recs['waste'])
                
            except Exception as e:
                logger.error(f"Error generating recommendations for {meal_type}: {str(e)}")
        
        # Generate operational recommendations
        recommendations['operational_recommendations'] = self._generate_operational_recommendations(
            forecast_date, dining_hall
        )
        
        # Calculate potential cost savings
        recommendations['cost_savings'] = self._calculate_cost_savings(recommendations)
        
        # Prioritize actions
        recommendations['priority_actions'] = self._prioritize_actions(recommendations)
        
        return recommendations
    
    def _generate_meal_recommendations(self, demand_pred: Dict[str, Any], 
                                     waste_pred: Dict[str, Any], 
                                     meal_type: str) -> Dict[str, List[str]]:
        """Generate meal-specific recommendations."""
        recommendations = {
            'demand': [],
            'waste': []
        }
        
        predicted_demand = demand_pred.get('predicted_demand', 0)
        predicted_waste = waste_pred.get('total_predicted_waste', 0)
        category_waste = waste_pred.get('category_predictions', {})
        
        # Demand recommendations
        if predicted_demand > 0:
            demand_recs = self._generate_demand_recommendations(predicted_demand, meal_type)
            recommendations['demand'].extend(demand_recs)
        
        # Waste recommendations
        if predicted_waste > 0:
            waste_recs = self._generate_waste_recommendations(predicted_waste, category_waste, meal_type)
            recommendations['waste'].extend(waste_recs)
        
        return recommendations
    
    def _generate_demand_recommendations(self, predicted_demand: int, meal_type: str) -> List[str]:
        """Generate demand-related recommendations."""
        recommendations = []
        
        # Base demand levels by meal type
        demand_levels = {
            'breakfast': {'low': 150, 'medium': 300, 'high': 500},
            'lunch': {'low': 300, 'medium': 600, 'high': 1000},
            'dinner': {'low': 250, 'medium': 500, 'high': 800}
        }
        
        levels = demand_levels.get(meal_type, {'low': 200, 'medium': 400, 'high': 700})
        
        if predicted_demand < levels['low']:
            recommendations.append(f"Low demand predicted for {meal_type} ({predicted_demand} servings)")
            recommendations.append("Consider reducing staff scheduling and preparation quantities")
            recommendations.append("Focus on high-margin, popular items to maximize revenue")
        
        elif predicted_demand > levels['high']:
            recommendations.append(f"High demand predicted for {meal_type} ({predicted_demand} servings)")
            recommendations.append("Ensure adequate staffing and inventory levels")
            recommendations.append("Consider express service options to handle peak demand")
            recommendations.append("Prepare popular items in larger batches")
        
        else:
            recommendations.append(f"Moderate demand predicted for {meal_type} ({predicted_demand} servings)")
            recommendations.append("Maintain standard preparation quantities")
            recommendations.append("Monitor demand trends throughout service period")
        
        # Menu-specific recommendations
        if meal_type == 'lunch':
            recommendations.append("Lunch typically has highest demand - ensure adequate variety")
        elif meal_type == 'breakfast':
            recommendations.append("Consider grab-and-go options for busy morning periods")
        elif meal_type == 'dinner':
            recommendations.append("Dinner demand may vary - monitor patterns closely")
        
        return recommendations
    
    def _generate_waste_recommendations(self, predicted_waste: float, 
                                     category_waste: Dict[str, float], 
                                     meal_type: str) -> List[str]:
        """Generate waste-related recommendations."""
        recommendations = []
        
        if predicted_waste > 0:
            # Overall waste recommendations
            waste_percentage = (predicted_waste / 100) * 10  # Assume 10% waste rate
            
            if waste_percentage > 15:
                recommendations.append(f"High waste predicted ({predicted_waste:.1f} kg, {waste_percentage:.1f}%)")
                recommendations.append("Implement stricter portion control")
                recommendations.append("Consider smaller batch sizes")
                recommendations.append("Review preparation methods for efficiency")
            
            elif waste_percentage > 10:
                recommendations.append(f"Moderate waste predicted ({predicted_waste:.1f} kg, {waste_percentage:.1f}%)")
                recommendations.append("Monitor portion sizes carefully")
                recommendations.append("Consider demand-driven preparation")
            
            else:
                recommendations.append(f"Low waste predicted ({predicted_waste:.1f} kg, {waste_percentage:.1f}%)")
                recommendations.append("Maintain current waste reduction practices")
        
        # Category-specific recommendations
        if category_waste:
            # Find highest waste categories
            sorted_categories = sorted(category_waste.items(), key=lambda x: x[1], reverse=True)
            
            for category, waste_amount in sorted_categories[:3]:
                if waste_amount > 2:  # Only recommend for significant waste
                    reduction_percentage = min(50, int(waste_amount / 2))
                    recommendations.append(f"Reduce {category} preparation by {reduction_percentage}%")
                    
                    # Specific category recommendations
                    if category == 'Vegetables':
                        recommendations.append("Consider fresh preparation closer to service time")
                    elif category == 'Grains':
                        recommendations.append("Prepare grains in smaller batches")
                    elif category == 'Meat':
                        recommendations.append("Implement precise portion control for meat items")
                    elif category == 'Dairy':
                        recommendations.append("Monitor dairy product freshness and usage")
        
        return recommendations
    
    def _generate_operational_recommendations(self, forecast_date: date, dining_hall: str) -> List[str]:
        """Generate operational recommendations."""
        recommendations = []
        
        # Day of week considerations
        day_of_week = forecast_date.weekday()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        if day_of_week == 4:  # Friday
            recommendations.append("Friday typically has higher demand - prepare extra quantities")
            recommendations.append("Consider weekend preparation for Saturday")
        elif day_of_week == 5:  # Saturday
            recommendations.append("Weekend demand patterns may differ from weekdays")
            recommendations.append("Adjust staffing levels for weekend service")
        elif day_of_week == 6:  # Sunday
            recommendations.append("Sunday often has lower demand - reduce preparation")
            recommendations.append("Plan for Monday preparation needs")
        
        # Weather considerations
        weather_impact = self._get_weather_impact(forecast_date)
        if weather_impact['factor'] != 'normal':
            recommendations.append(f"Weather impact: {weather_impact['description']}")
            recommendations.append(weather_impact['recommendation'])
        
        # Academic calendar considerations
        academic_period = self._get_academic_period(forecast_date)
        if academic_period != 'normal':
            recommendations.append(f"Academic period: {academic_period['description']}")
            recommendations.append(academic_period['recommendation'])
        
        # Staff scheduling recommendations
        staffing_recs = self._generate_staffing_recommendations(forecast_date, dining_hall)
        recommendations.extend(staffing_recs)
        
        return recommendations
    
    def _get_weather_impact(self, forecast_date: date) -> Dict[str, str]:
        """Get weather impact recommendations."""
        # Simplified weather impact (in production, this would use actual weather API)
        month = forecast_date.month
        
        if month in [12, 1, 2]:  # Winter
            return {
                'factor': 'cold_weather',
                'description': 'Cold weather expected',
                'recommendation': 'Prepare more hot, comforting dishes'
            }
        elif month in [6, 7, 8]:  # Summer
            return {
                'factor': 'hot_weather',
                'description': 'Hot weather expected',
                'recommendation': 'Focus on lighter, refreshing options'
            }
        else:
            return {
                'factor': 'normal',
                'description': 'Normal weather conditions',
                'recommendation': 'Standard menu planning'
            }
    
    def _get_academic_period(self, forecast_date: date) -> Dict[str, str]:
        """Get academic period recommendations."""
        month = forecast_date.month
        day = forecast_date.day
        
        if (month == 12 and day >= 20) or (month == 1 and day <= 15):
            return {
                'description': 'Winter break period',
                'recommendation': 'Reduce preparation quantities significantly'
            }
        elif month in [6, 7, 8]:
            return {
                'description': 'Summer break period',
                'recommendation': 'Expect reduced student population'
            }
        elif month in [5, 10, 12] and 15 <= day <= 25:
            return {
                'description': 'Exam period',
                'recommendation': 'Prepare more grab-and-go options for studying students'
            }
        else:
            return {
                'description': 'Normal academic period',
                'recommendation': 'Standard preparation quantities'
            }
    
    def _generate_staffing_recommendations(self, forecast_date: date, dining_hall: str) -> List[str]:
        """Generate staffing recommendations."""
        recommendations = []
        
        # Get predicted demand for all meals
        total_demand = 0
        meal_types = ['breakfast', 'lunch', 'dinner']
        
        for meal_type in meal_types:
            try:
                demand_pred = self.demand_predictor.predict_meal_demand(forecast_date, dining_hall, meal_type)
                total_demand += demand_pred.get('predicted_demand', 0)
            except:
                continue
        
        # Staffing recommendations based on total demand
        if total_demand < 500:
            recommendations.append("Low demand expected - minimum staffing required")
            recommendations.append("Consider cross-training staff for flexibility")
        elif total_demand > 1500:
            recommendations.append("High demand expected - maximum staffing required")
            recommendations.append("Schedule additional staff for peak periods")
        else:
            recommendations.append("Moderate demand expected - standard staffing")
        
        # Peak time recommendations
        recommendations.append("Ensure adequate staffing during peak service hours")
        recommendations.append("Schedule breaks during low-demand periods")
        
        return recommendations
    
    def _calculate_cost_savings(self, recommendations: Dict[str, Any]) -> Dict[str, float]:
        """Calculate potential cost savings from recommendations."""
        savings = {
            'waste_reduction': 0.0,
            'labor_optimization': 0.0,
            'inventory_optimization': 0.0,
            'total_savings': 0.0
        }
        
        # Waste reduction savings
        waste_recs = recommendations.get('waste_recommendations', [])
        if waste_recs:
            # Assume each waste recommendation saves $10-50
            savings['waste_reduction'] = len(waste_recs) * 25.0
        
        # Labor optimization savings
        operational_recs = recommendations.get('operational_recommendations', [])
        staffing_recs = [rec for rec in operational_recs if 'staff' in rec.lower()]
        if staffing_recs:
            # Assume each staffing recommendation saves $50-100
            savings['labor_optimization'] = len(staffing_recs) * 75.0
        
        # Inventory optimization savings
        demand_recs = recommendations.get('demand_recommendations', [])
        inventory_recs = [rec for rec in demand_recs if 'reduce' in rec.lower() or 'inventory' in rec.lower()]
        if inventory_recs:
            # Assume each inventory recommendation saves $15-30
            savings['inventory_optimization'] = len(inventory_recs) * 22.5
        
        # Calculate total savings
        savings['total_savings'] = (
            savings['waste_reduction'] + 
            savings['labor_optimization'] + 
            savings['inventory_optimization']
        )
        
        return savings
    
    def _prioritize_actions(self, recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize recommendations by impact and urgency."""
        priority_actions = []
        
        # Combine all recommendations with priority scores
        all_recs = []
        
        # Demand recommendations (high priority for revenue)
        for rec in recommendations.get('demand_recommendations', []):
            priority = self._calculate_priority(rec, 'demand')
            all_recs.append({'action': rec, 'priority': priority, 'category': 'demand'})
        
        # Waste recommendations (high priority for cost)
        for rec in recommendations.get('waste_recommendations', []):
            priority = self._calculate_priority(rec, 'waste')
            all_recs.append({'action': rec, 'priority': priority, 'category': 'waste'})
        
        # Operational recommendations (medium priority)
        for rec in recommendations.get('operational_recommendations', []):
            priority = self._calculate_priority(rec, 'operational')
            all_recs.append({'action': rec, 'priority': priority, 'category': 'operational'})
        
        # Sort by priority (higher = more urgent)
        all_recs.sort(key=lambda x: x['priority'], reverse=True)
        
        # Take top 10 actions
        priority_actions = all_recs[:10]
        
        return priority_actions
    
    def _calculate_priority(self, recommendation: str, category: str) -> int:
        """Calculate priority score for recommendation."""
        score = 5  # Base score
        
        # Category-specific scoring
        if category == 'waste':
            score += 3  # Waste is high priority
        elif category == 'demand':
            score += 2  # Demand is medium-high priority
        elif category == 'operational':
            score += 1  # Operational is medium priority
        
        # Content-based scoring
        recommendation_lower = recommendation.lower()
        
        # High-impact keywords
        if any(keyword in recommendation_lower for keyword in ['high', 'reduce', 'increase', 'critical']):
            score += 2
        
        # Medium-impact keywords
        if any(keyword in recommendation_lower for keyword in ['moderate', 'adjust', 'monitor']):
            score += 1
        
        # Low-impact keywords
        if any(keyword in recommendation_lower for keyword in ['maintain', 'consider', 'review']):
            score -= 1
        
        # Urgency keywords
        if any(keyword in recommendation_lower for keyword in ['immediate', 'urgent', 'asap']):
            score += 3
        
        # Cost-related keywords
        if any(keyword in recommendation_lower for keyword in ['cost', 'savings', 'revenue']):
            score += 2
        
        return max(1, min(10, score))  # Ensure score is between 1 and 10
    
    def generate_menu_optimization_recommendations(self, forecast_date: date, 
                                                dining_hall: str,
                                                current_menu: List[str]) -> Dict[str, Any]:
        """Generate menu optimization recommendations."""
        logger.info(f"Generating menu optimization for {forecast_date}")
        
        recommendations = {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'current_menu': current_menu,
            'menu_optimizations': [],
            'item_recommendations': {},
            'predicted_popularity': {},
            'cost_optimizations': []
        }
        
        # Predict demand for each menu item
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            try:
                demand_pred = self.demand_predictor.predict_meal_demand(
                    forecast_date, dining_hall, meal_type, current_menu
                )
                
                if 'menu_predictions' in demand_pred:
                    menu_predictions = demand_pred['menu_predictions']
                    
                    # Generate item-specific recommendations
                    for item, predicted_demand in menu_predictions.items():
                        item_rec = self._generate_item_recommendation(item, predicted_demand)
                        recommendations['item_recommendations'][item] = item_rec
                        
                        # Predict popularity
                        popularity = self._predict_item_popularity(predicted_demand, meal_type)
                        recommendations['predicted_popularity'][item] = popularity
                
            except Exception as e:
                logger.error(f"Error generating menu optimization for {meal_type}: {str(e)}")
        
        # Generate overall menu optimizations
        recommendations['menu_optimizations'] = self._generate_menu_optimizations(
            recommendations['item_recommendations']
        )
        
        # Generate cost optimizations
        recommendations['cost_optimizations'] = self._generate_cost_optimizations(
            recommendations['item_recommendations']
        )
        
        return recommendations
    
    def _generate_item_recommendation(self, item: str, predicted_demand: int) -> Dict[str, Any]:
        """Generate recommendation for specific menu item."""
        recommendation = {
            'item': item,
            'predicted_demand': predicted_demand,
            'recommendation': '',
            'action': 'maintain',
            'confidence': 0.8
        }
        
        if predicted_demand < 10:
            recommendation['recommendation'] = f"Low demand predicted for {item} ({predicted_demand} servings)"
            recommendation['action'] = 'reduce_or_remove'
            recommendation['confidence'] = 0.9
        elif predicted_demand > 100:
            recommendation['recommendation'] = f"High demand predicted for {item} ({predicted_demand} servings)"
            recommendation['action'] = 'increase_preparation'
            recommendation['confidence'] = 0.9
        else:
            recommendation['recommendation'] = f"Moderate demand predicted for {item} ({predicted_demand} servings)"
            recommendation['action'] = 'maintain'
            recommendation['confidence'] = 0.7
        
        # Add specific item recommendations
        item_lower = item.lower()
        
        if 'vegetarian' in item_lower or 'vegan' in item_lower:
            recommendation['recommendation'] += " - Consider promoting for health-conscious students"
        elif 'chicken' in item_lower or 'beef' in item_lower:
            recommendation['recommendation'] += " - Ensure proper portion control for cost management"
        elif 'salad' in item_lower:
            recommendation['recommendation'] += " - Prepare fresh near service time"
        
        return recommendation
    
    def _predict_item_popularity(self, predicted_demand: int, meal_type: str) -> str:
        """Predict item popularity based on demand."""
        # Normalize demand to popularity scale
        demand_levels = {
            'breakfast': {'low': 20, 'medium': 50, 'high': 100},
            'lunch': {'low': 40, 'medium': 100, 'high': 200},
            'dinner': {'low': 30, 'medium': 75, 'high': 150}
        }
        
        levels = demand_levels.get(meal_type, {'low': 30, 'medium': 75, 'high': 150})
        
        if predicted_demand < levels['low']:
            return 'Low'
        elif predicted_demand > levels['high']:
            return 'High'
        else:
            return 'Medium'
    
    def _generate_menu_optimizations(self, item_recommendations: Dict[str, Any]) -> List[str]:
        """Generate overall menu optimization recommendations."""
        optimizations = []
        
        # Analyze item recommendations
        high_demand_items = []
        low_demand_items = []
        
        for item, rec in item_recommendations.items():
            if rec['action'] == 'increase_preparation':
                high_demand_items.append(item)
            elif rec['action'] == 'reduce_or_remove':
                low_demand_items.append(item)
        
        # Generate optimization recommendations
        if high_demand_items:
            optimizations.append(f"Focus on high-demand items: {', '.join(high_demand_items[:3])}")
            optimizations.append("Ensure adequate preparation capacity for popular items")
        
        if low_demand_items:
            optimizations.append(f"Consider removing low-demand items: {', '.join(low_demand_items[:3])}")
            optimizations.append("Replace unpopular items with more popular alternatives")
        
        if not high_demand_items and not low_demand_items:
            optimizations.append("Current menu appears well-balanced")
            optimizations.append("Monitor demand trends for future optimizations")
        
        return optimizations
    
    def _generate_cost_optimizations(self, item_recommendations: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations."""
        optimizations = []
        
        # Cost-related recommendations
        optimizations.append("Review ingredient costs for high-demand items")
        optimizations.append("Consider bulk purchasing for frequently used ingredients")
        optimizations.append("Implement portion control for high-cost items")
        
        # Waste reduction recommendations
        optimizations.append("Focus on reducing waste for expensive ingredients")
        optimizations.append("Consider using leftovers in creative ways")
        optimizations.append("Implement just-in-time preparation for perishable items")
        
        return optimizations


# Convenience functions for direct use
def generate_daily_recommendations(forecast_date: date, dining_hall: str) -> Dict[str, Any]:
    """Generate daily recommendations."""
    engine = RecommendationEngine()
    return engine.generate_daily_recommendations(forecast_date, dining_hall)


def generate_menu_recommendations(forecast_date: date, dining_hall: str, 
                                current_menu: List[str]) -> Dict[str, Any]:
    """Generate menu optimization recommendations."""
    engine = RecommendationEngine()
    return engine.generate_menu_optimization_recommendations(forecast_date, dining_hall, current_menu)
