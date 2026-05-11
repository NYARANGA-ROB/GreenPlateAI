"""
Helper functions for Food Waste Logging module.

This module provides reusable utility functions for data processing,
formatting, calculations, and common operations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging
import json

from database.models import FoodWasteLog, WasteCategory, MealType
from waste_logging.database_ops import WasteLoggingDB

logger = logging.getLogger(__name__)


class WasteLoggingHelpers:
    """Helper functions for waste logging operations."""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "$") -> str:
        """Format currency amount."""
        if amount is None:
            return f"{currency}0.00"
        return f"{currency}{amount:,.2f}"
    
    @staticmethod
    def format_weight(weight_kg: float) -> str:
        """Format weight with appropriate units."""
        if weight_kg is None:
            return "0.0 kg"
        
        if weight_kg >= 1000:
            return f"{weight_kg/1000:.2f} tons"
        elif weight_kg >= 1:
            return f"{weight_kg:.2f} kg"
        else:
            return f"{weight_kg*1000:.0f} g"
    
    @staticmethod
    def format_percentage(value: float, decimal_places: int = 1) -> str:
        """Format percentage."""
        if value is None:
            return "0.0%"
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def calculate_waste_percentage(prepared: float, served: float) -> float:
        """Calculate waste percentage."""
        if prepared is None or prepared <= 0:
            return 0.0
        if served is None:
            served = 0.0
        
        waste = prepared - served
        return (waste / prepared) * 100 if prepared > 0 else 0.0
    
    @staticmethod
    def calculate_cost_efficiency(estimated_cost: float, actual_cost: float) -> float:
        """Calculate cost efficiency percentage."""
        if estimated_cost is None or estimated_cost <= 0:
            return 0.0
        if actual_cost is None:
            actual_cost = 0.0
        
        return (actual_cost / estimated_cost) * 100
    
    @staticmethod
    def get_waste_category_color(category: str) -> str:
        """Get color for waste category."""
        colors = {
            'preparation': '#FF6B6B',      # Red
            'plate_waste': '#4ECDC4',     # Teal
            'spoilage': '#FFA500',        # Orange
            'expired': '#FF4444',         # Dark Red
            'overproduction': '#FFD93D',  # Yellow
            'other': '#95E1D3'           # Light Green
        }
        return colors.get(category, '#95E1D3')
    
    @staticmethod
    def get_meal_type_emoji(meal_type: str) -> str:
        """Get emoji for meal type."""
        emojis = {
            'breakfast': '🍳',
            'lunch': '🍽️',
            'dinner': '🍽️',
            'snack': '🍪'
        }
        return emojis.get(meal_type, '🍽️')
    
    @staticmethod
    def get_waste_category_emoji(category: str) -> str:
        """Get emoji for waste category."""
        emojis = {
            'preparation': '👨‍🍳',
            'plate_waste': '🍽️',
            'spoilage': '🦠',
            'expired': '⏰',
            'overproduction': '📈',
            'other': '📦'
        }
        return emojis.get(category, '📦')
    
    @staticmethod
    def calculate_environmental_impact(category: str, quantity_kg: float) -> Dict[str, float]:
        """Calculate environmental impact metrics."""
        # Impact factors by category
        co2_factors = {
            'Meat': 27.0,
            'Dairy': 13.5,
            'Vegetables': 2.0,
            'Fruits': 1.5,
            'Grains': 2.5,
            'Seafood': 20.0,
            'Processed': 10.0,
            'Other': 5.0
        }
        
        water_factors = {
            'Meat': 15000,
            'Dairy': 1000,
            'Vegetables': 300,
            'Fruits': 800,
            'Grains': 1600,
            'Seafood': 5000,
            'Processed': 2000,
            'Other': 1000
        }
        
        land_factors = {
            'Meat': 200,
            'Dairy': 50,
            'Vegetables': 10,
            'Fruits': 15,
            'Grains': 25,
            'Seafood': 30,
            'Processed': 40,
            'Other': 20
        }
        
        co2_impact = quantity_kg * co2_factors.get(category, 5.0)
        water_impact = quantity_kg * water_factors.get(category, 1000)
        land_impact = quantity_kg * land_factors.get(category, 20)
        
        return {
            'co2_kg': co2_impact,
            'water_liters': water_impact,
            'land_m2': land_impact
        }
    
    @staticmethod
    def get_waste_severity_level(waste_percentage: float) -> str:
        """Get waste severity level based on percentage."""
        if waste_percentage >= 30:
            return "Critical"
        elif waste_percentage >= 20:
            return "High"
        elif waste_percentage >= 10:
            return "Medium"
        elif waste_percentage >= 5:
            return "Low"
        else:
            return "Minimal"
    
    @staticmethod
    def get_severity_color(severity: str) -> str:
        """Get color for severity level."""
        colors = {
            'Critical': '#DC3545',  # Red
            'High': '#FD7E14',      # Orange
            'Medium': '#FFC107',    # Yellow
            'Low': '#20C997',       # Teal
            'Minimal': '#28A745'    # Green
        }
        return colors.get(severity, '#6C757D')
    
    @staticmethod
    def generate_waste_summary(waste_logs: List[FoodWasteLog]) -> Dict[str, Any]:
        """Generate comprehensive waste summary."""
        if not waste_logs:
            return {
                'total_waste_kg': 0,
                'total_cost': 0,
                'total_entries': 0,
                'category_breakdown': {},
                'daily_average': 0,
                'top_items': [],
                'environmental_impact': {
                    'co2_kg': 0,
                    'water_liters': 0,
                    'land_m2': 0
                }
            }
        
        total_waste = sum(log.quantity_kg for log in waste_logs)
        total_cost = sum(log.estimated_cost or 0 for log in waste_logs)
        
        # Category breakdown
        category_breakdown = {}
        for log in waste_logs:
            if log.category not in category_breakdown:
                category_breakdown[log.category] = {
                    'quantity_kg': 0,
                    'cost': 0,
                    'count': 0
                }
            
            category_breakdown[log.category]['quantity_kg'] += log.quantity_kg
            category_breakdown[log.category]['cost'] += log.estimated_cost or 0
            category_breakdown[log.category]['count'] += 1
        
        # Top waste items
        item_totals = {}
        for log in waste_logs:
            if log.food_item not in item_totals:
                item_totals[log.food_item] = 0
            item_totals[log.food_item] += log.quantity_kg
        
        top_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Environmental impact
        total_co2 = 0
        total_water = 0
        total_land = 0
        
        for log in waste_logs:
            impact = WasteLoggingHelpers.calculate_environmental_impact(
                log.category, log.quantity_kg
            )
            total_co2 += impact['co2_kg']
            total_water += impact['water_liters']
            total_land += impact['land_m2']
        
        # Daily average (if multiple dates)
        dates = set(log.waste_date for log in waste_logs)
        daily_average = total_waste / len(dates) if dates else 0
        
        return {
            'total_waste_kg': total_waste,
            'total_cost': total_cost,
            'total_entries': len(waste_logs),
            'category_breakdown': category_breakdown,
            'daily_average': daily_average,
            'top_items': top_items,
            'environmental_impact': {
                'co2_kg': total_co2,
                'water_liters': total_water,
                'land_m2': total_land
            }
        }
    
    @staticmethod
    def create_waste_dataframe(waste_logs: List[FoodWasteLog]) -> pd.DataFrame:
        """Create pandas DataFrame from waste logs."""
        if not waste_logs:
            return pd.DataFrame()
        
        data = []
        for log in waste_logs:
            data.append({
                'id': log.id,
                'food_item': log.food_item,
                'category': log.category,
                'waste_category': log.waste_category.value,
                'quantity_kg': log.quantity_kg,
                'estimated_cost': log.estimated_cost or 0,
                'dining_hall': log.dining_hall,
                'meal_period': log.meal_period.value if log.meal_period else 'N/A',
                'waste_date': log.waste_date.isoformat(),
                'waste_time': log.waste_time.isoformat(),
                'reason': log.reason or 'N/A',
                'temperature': log.temperature or 'N/A',
                'recorded_by': log.recorded_by or 'N/A'
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def filter_waste_logs(
        waste_logs: List[FoodWasteLog],
        start_date: date = None,
        end_date: date = None,
        dining_hall: str = None,
        waste_category: WasteCategory = None,
        food_category: str = None
    ) -> List[FoodWasteLog]:
        """Filter waste logs based on criteria."""
        filtered_logs = waste_logs.copy()
        
        if start_date:
            filtered_logs = [log for log in filtered_logs if log.waste_date >= start_date]
        
        if end_date:
            filtered_logs = [log for log in filtered_logs if log.waste_date <= end_date]
        
        if dining_hall:
            filtered_logs = [log for log in filtered_logs if log.dining_hall == dining_hall]
        
        if waste_category:
            filtered_logs = [log for log in filtered_logs if log.waste_category == waste_category]
        
        if food_category:
            filtered_logs = [log for log in filtered_logs if log.category == food_category]
        
        return filtered_logs
    
    @staticmethod
    def get_date_range_preset(preset: str) -> Tuple[date, date]:
        """Get date range for preset periods."""
        today = date.today()
        
        if preset == "Today":
            return today, today
        elif preset == "Yesterday":
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        elif preset == "Last 7 Days":
            return today - timedelta(days=6), today
        elif preset == "Last 30 Days":
            return today - timedelta(days=29), today
        elif preset == "This Week":
            start_of_week = today - timedelta(days=today.weekday())
            return start_of_week, today
        elif preset == "Last Week":
            start_of_last_week = today - timedelta(days=today.weekday() + 7)
            end_of_last_week = start_of_last_week + timedelta(days=6)
            return start_of_last_week, end_of_last_week
        elif preset == "This Month":
            start_of_month = today.replace(day=1)
            return start_of_month, today
        elif preset == "Last Month":
            if today.month == 1:
                start_of_last_month = today.replace(year=today.year - 1, month=12, day=1)
                end_of_last_month = today.replace(year=today.year - 1, month=12, day=31)
            else:
                start_of_last_month = today.replace(month=today.month - 1, day=1)
                # Calculate last day of previous month
                next_month = today.replace(month=today.month + 1, day=1)
                end_of_last_month = next_month - timedelta(days=1)
            return start_of_last_month, end_of_last_month
        else:
            # Default to last 30 days
            return today - timedelta(days=29), today
    
    @staticmethod
    def export_to_csv(waste_logs: List[FoodWasteLog], filename: str = None) -> str:
        """Export waste logs to CSV."""
        if filename is None:
            filename = f"waste_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        df = WasteLoggingHelpers.create_waste_dataframe(waste_logs)
        
        if not df.empty:
            df.to_csv(filename, index=False)
            logger.info(f"Waste logs exported to {filename}")
        
        return filename
    
    @staticmethod
    def export_to_excel(waste_logs: List[FoodWasteLog], filename: str = None) -> str:
        """Export waste logs to Excel with multiple sheets."""
        if filename is None:
            filename = f"waste_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main waste logs sheet
                df = WasteLoggingHelpers.create_waste_dataframe(waste_logs)
                if not df.empty:
                    df.to_excel(writer, sheet_name='Waste Logs', index=False)
                
                # Summary sheet
                summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
                
                # Create summary dataframe
                summary_data = [
                    ['Total Waste (kg)', summary['total_waste_kg']],
                    ['Total Cost', summary['total_cost']],
                    ['Total Entries', summary['total_entries']],
                    ['Daily Average (kg)', summary['daily_average']],
                    ['Total CO2 Impact (kg)', summary['environmental_impact']['co2_kg']],
                    ['Total Water Footprint (L)', summary['environmental_impact']['water_liters']],
                    ['Total Land Use (m²)', summary['environmental_impact']['land_m2']]
                ]
                
                summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Category breakdown sheet
                if summary['category_breakdown']:
                    category_data = []
                    for category, data in summary['category_breakdown'].items():
                        category_data.append([
                            category,
                            data['quantity_kg'],
                            data['cost'],
                            data['count']
                        ])
                    
                    category_df = pd.DataFrame(
                        category_data,
                        columns=['Category', 'Quantity (kg)', 'Cost', 'Count']
                    )
                    category_df.to_excel(writer, sheet_name='Categories', index=False)
                
                # Top items sheet
                if summary['top_items']:
                    top_items_df = pd.DataFrame(
                        summary['top_items'],
                        columns=['Food Item', 'Quantity (kg)']
                    )
                    top_items_df.to_excel(writer, sheet_name='Top Items', index=False)
            
            logger.info(f"Waste logs exported to Excel: {filename}")
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            # Fallback to CSV
            return WasteLoggingHelpers.export_to_csv(waste_logs, filename.replace('.xlsx', '.csv'))
        
        return filename
    
    @staticmethod
    def calculate_waste_trends(waste_logs: List[FoodWasteLog], days: int = 30) -> Dict[str, Any]:
        """Calculate waste trends over time."""
        if not waste_logs:
            return {'trend': 'stable', 'change_percentage': 0, 'data': []}
        
        # Group by date
        daily_data = {}
        for log in waste_logs:
            date_str = log.waste_date.isoformat()
            if date_str not in daily_data:
                daily_data[date_str] = 0
            daily_data[date_str] += log.quantity_kg
        
        # Sort by date
        sorted_dates = sorted(daily_data.keys())
        
        # Calculate trend
        if len(sorted_dates) < 2:
            return {'trend': 'stable', 'change_percentage': 0, 'data': []}
        
        # Get first and last values for comparison
        first_value = daily_data[sorted_dates[0]]
        last_value = daily_data[sorted_dates[-1]]
        
        if first_value == 0:
            change_percentage = 0
        else:
            change_percentage = ((last_value - first_value) / first_value) * 100
        
        # Determine trend
        if change_percentage > 10:
            trend = 'increasing'
        elif change_percentage < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        # Prepare data for charting
        trend_data = []
        for date_str in sorted_dates:
            trend_data.append({
                'date': date_str,
                'waste_kg': daily_data[date_str]
            })
        
        return {
            'trend': trend,
            'change_percentage': change_percentage,
            'data': trend_data
        }
    
    @staticmethod
    def get_waste_recommendations(waste_logs: List[FoodWasteLog]) -> List[str]:
        """Generate waste reduction recommendations."""
        recommendations = []
        
        if not waste_logs:
            return recommendations
        
        summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
        
        # Analyze top waste items
        if summary['top_items']:
            top_item, top_quantity = summary['top_items'][0]
            recommendations.append(f"Focus on reducing waste for {top_item} ({top_quantity:.2f} kg) - consider smaller batches or better forecasting")
        
        # Analyze waste categories
        if summary['category_breakdown']:
            worst_category = max(summary['category_breakdown'].items(), key=lambda x: x[1]['quantity_kg'])
            recommendations.append(f"{worst_category[0]} category has highest waste ({worst_category[1]['quantity_kg']:.2f} kg) - review preparation methods")
        
        # Analyze overall waste level
        if summary['daily_average'] > 50:
            recommendations.append("Daily waste average is high (>50kg) - implement stricter portion control")
        elif summary['daily_average'] > 30:
            recommendations.append("Daily waste average is moderate (>30kg) - consider demand forecasting improvements")
        
        # Check for overproduction patterns
        overproduction_waste = [log for log in waste_logs if log.waste_category == WasteCategory.OVERPRODUCTION]
        if len(overproduction_waste) > len(waste_logs) * 0.3:  # More than 30% overproduction
            recommendations.append("High overproduction detected - improve demand forecasting and reduce batch sizes")
        
        # Check for spoilage
        spoilage_waste = [log for log in waste_logs if log.waste_category == WasteCategory.SPOILAGE]
        if len(spoilage_waste) > len(waste_logs) * 0.2:  # More than 20% spoilage
            recommendations.append("High spoilage detected - review storage conditions and inventory management")
        
        return recommendations
    
    @staticmethod
    def format_duration_hours(start_time: datetime, end_time: datetime) -> str:
        """Format duration between two times."""
        if not start_time or not end_time:
            return "N/A"
        
        duration = end_time - start_time
        hours = duration.total_seconds() / 3600
        
        if hours < 1:
            minutes = duration.total_seconds() / 60
            return f"{minutes:.0f} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            return f"{days:.1f} days"
    
    @staticmethod
    def calculate_waste_score(waste_logs: List[FoodWasteLog]) -> Dict[str, Any]:
        """Calculate waste performance score."""
        if not waste_logs:
            return {'score': 0, 'grade': 'F', 'factors': {}}
        
        summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
        
        # Factors affecting score (0-100 scale)
        factors = {}
        
        # Daily waste factor (lower is better)
        daily_waste = summary['daily_average']
        if daily_waste <= 10:
            factors['daily_waste'] = 100
        elif daily_waste <= 25:
            factors['daily_waste'] = 80
        elif daily_waste <= 50:
            factors['daily_waste'] = 60
        elif daily_waste <= 75:
            factors['daily_waste'] = 40
        else:
            factors['daily_waste'] = 20
        
        # Cost efficiency factor
        if summary['total_cost'] > 0:
            cost_per_kg = summary['total_cost'] / summary['total_waste_kg']
            if cost_per_kg <= 2:
                factors['cost_efficiency'] = 100
            elif cost_per_kg <= 5:
                factors['cost_efficiency'] = 80
            elif cost_per_kg <= 10:
                factors['cost_efficiency'] = 60
            else:
                factors['cost_efficiency'] = 40
        else:
            factors['cost_efficiency'] = 100
        
        # Category diversity factor (more diverse waste is worse)
        category_count = len(summary['category_breakdown'])
        if category_count <= 2:
            factors['category_diversity'] = 100
        elif category_count <= 4:
            factors['category_diversity'] = 80
        elif category_count <= 6:
            factors['category_diversity'] = 60
        else:
            factors['category_diversity'] = 40
        
        # Consistency factor (less variation is better)
        if len(summary['top_items']) > 0:
            top_item_percentage = (summary['top_items'][0][1] / summary['total_waste_kg']) * 100
            if top_item_percentage >= 50:
                factors['consistency'] = 100
            elif top_item_percentage >= 30:
                factors['consistency'] = 80
            elif top_item_percentage >= 15:
                factors['consistency'] = 60
            else:
                factors['consistency'] = 40
        else:
            factors['consistency'] = 100
        
        # Calculate overall score
        overall_score = sum(factors.values()) / len(factors)
        
        # Determine grade
        if overall_score >= 90:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'B'
        elif overall_score >= 70:
            grade = 'C'
        elif overall_score >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'score': round(overall_score, 1),
            'grade': grade,
            'factors': factors
        }


# Convenience functions for direct use
def format_currency(amount: float, currency: str = "$") -> str:
    """Format currency amount."""
    return WasteLoggingHelpers.format_currency(amount, currency)


def format_weight(weight_kg: float) -> str:
    """Format weight with appropriate units."""
    return WasteLoggingHelpers.format_weight(weight_kg)


def calculate_waste_percentage(prepared: float, served: float) -> float:
    """Calculate waste percentage."""
    return WasteLoggingHelpers.calculate_waste_percentage(prepared, served)


def generate_waste_summary(waste_logs: List[FoodWasteLog]) -> Dict[str, Any]:
    """Generate comprehensive waste summary."""
    return WasteLoggingHelpers.generate_waste_summary(waste_logs)


def create_waste_dataframe(waste_logs: List[FoodWasteLog]) -> pd.DataFrame:
    """Create pandas DataFrame from waste logs."""
    return WasteLoggingHelpers.create_waste_dataframe(waste_logs)
