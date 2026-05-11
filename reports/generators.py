"""
Report generators for GreenPlateAI.

This module provides functions for generating various types of reports
including waste reports, cost analysis, efficiency reports, and summaries.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any, Tuple
import logging
from io import BytesIO
import base64

from database.connection import get_session
from models.waste_record import WasteRecord
from models.prediction import Prediction
from utils.helpers import format_currency, format_weight, format_percentage

logger = logging.getLogger(__name__)


def generate_waste_report(
    start_date: date,
    end_date: date,
    report_format: str = 'dataframe'
) -> Any:
    """
    Generate comprehensive waste report.
    
    Args:
        start_date: Report start date
        end_date: Report end date
        report_format: Output format ('dataframe', 'dict', 'html')
        
    Returns:
        Report data in specified format
    """
    try:
        logger.info(f"Generating waste report from {start_date} to {end_date}")
        
        # Get waste data
        waste_data = get_waste_data_for_period(start_date, end_date)
        
        if waste_data.empty:
            return create_empty_report("No waste data available for the specified period")
        
        # Generate report sections
        report = {
            'metadata': {
                'report_type': 'Waste Analysis Report',
                'period': f"{start_date} to {end_date}",
                'generated_at': datetime.utcnow(),
                'total_records': len(waste_data)
            },
            'summary': generate_waste_summary(waste_data),
            'category_analysis': generate_category_analysis(waste_data),
            'source_analysis': generate_source_analysis(waste_data),
            'temporal_analysis': generate_temporal_analysis(waste_data),
            'detailed_data': waste_data.to_dict('records')
        }
        
        # Format output
        if report_format == 'dataframe':
            return format_report_as_dataframe(report)
        elif report_format == 'dict':
            return report
        elif report_format == 'html':
            return format_report_as_html(report)
        else:
            return report
        
    except Exception as e:
        logger.error(f"Error generating waste report: {e}")
        return create_error_report("Failed to generate waste report")


def generate_cost_report(
    start_date: date,
    end_date: date,
    report_format: str = 'dataframe'
) -> Any:
    """
    Generate cost analysis report.
    
    Args:
        start_date: Report start date
        end_date: Report end date
        report_format: Output format
        
    Returns:
        Cost report data
    """
    try:
        logger.info(f"Generating cost report from {start_date} to {end_date}")
        
        # Get waste data
        waste_data = get_waste_data_for_period(start_date, end_date)
        
        if waste_data.empty:
            return create_empty_report("No cost data available for the specified period")
        
        # Generate cost analysis
        report = {
            'metadata': {
                'report_type': 'Cost Analysis Report',
                'period': f"{start_date} to {end_date}",
                'generated_at': datetime.utcnow(),
                'total_records': len(waste_data)
            },
            'cost_summary': generate_cost_summary(waste_data),
            'cost_by_category': generate_cost_by_category(waste_data),
            'cost_trends': generate_cost_trends(waste_data),
            'cost_efficiency': generate_cost_efficiency(waste_data),
            'recommendations': generate_cost_recommendations(waste_data)
        }
        
        # Format output
        if report_format == 'dataframe':
            return format_report_as_dataframe(report)
        elif report_format == 'dict':
            return report
        elif report_format == 'html':
            return format_report_as_html(report)
        else:
            return report
        
    except Exception as e:
        logger.error(f"Error generating cost report: {e}")
        return create_error_report("Failed to generate cost report")


def generate_efficiency_report(
    start_date: date,
    end_date: date,
    report_format: str = 'dataframe'
) -> Any:
    """
    Generate efficiency analysis report.
    
    Args:
        start_date: Report start date
        end_date: Report end date
        report_format: Output format
        
    Returns:
        Efficiency report data
    """
    try:
        logger.info(f"Generating efficiency report from {start_date} to {end_date}")
        
        # Get waste data
        waste_data = get_waste_data_for_period(start_date, end_date)
        
        if waste_data.empty:
            return create_empty_report("No efficiency data available for the specified period")
        
        # Generate efficiency analysis
        report = {
            'metadata': {
                'report_type': 'Efficiency Analysis Report',
                'period': f"{start_date} to {end_date}",
                'generated_at': datetime.utcnow(),
                'total_records': len(waste_data)
            },
            'efficiency_metrics': generate_efficiency_metrics(waste_data),
            'performance_analysis': generate_performance_analysis(waste_data),
            'benchmarking': generate_benchmarking(waste_data),
            'improvement_opportunities': generate_improvement_opportunities(waste_data)
        }
        
        # Format output
        if report_format == 'dataframe':
            return format_report_as_dataframe(report)
        elif report_format == 'dict':
            return report
        elif report_format == 'html':
            return format_report_as_html(report)
        else:
            return report
        
    except Exception as e:
        logger.error(f"Error generating efficiency report: {e}")
        return create_error_report("Failed to generate efficiency report")


def generate_forecast_report(
    days_ahead: int = 7,
    model_type: str = 'xgboost',
    report_format: str = 'dataframe'
) -> Any:
    """
    Generate forecast report.
    
    Args:
        days_ahead: Number of days to forecast
        model_type: Model type for forecasting
        report_format: Output format
        
    Returns:
        Forecast report data
    """
    try:
        logger.info(f"Generating forecast report for {days_ahead} days using {model_type}")
        
        # Get forecast data
        forecast_data = get_forecast_data(days_ahead, model_type)
        
        if not forecast_data:
            return create_empty_report("No forecast data available")
        
        # Generate forecast analysis
        report = {
            'metadata': {
                'report_type': 'Forecast Report',
                'period': f"Next {days_ahead} days",
                'model_type': model_type,
                'generated_at': datetime.utcnow(),
                'total_forecasts': len(forecast_data)
            },
            'forecast_summary': generate_forecast_summary(forecast_data),
            'confidence_analysis': generate_confidence_analysis(forecast_data),
            'trend_analysis': generate_forecast_trend_analysis(forecast_data),
            'recommendations': generate_forecast_recommendations(forecast_data)
        }
        
        # Format output
        if report_format == 'dataframe':
            return format_report_as_dataframe(report)
        elif report_format == 'dict':
            return report
        elif report_format == 'html':
            return format_report_as_html(report)
        else:
            return report
        
    except Exception as e:
        logger.error(f"Error generating forecast report: {e}")
        return create_error_report("Failed to generate forecast report")


def generate_summary_report(
    days_back: int = 30,
    report_format: str = 'dataframe'
) -> Any:
    """
    Generate comprehensive summary report.
    
    Args:
        days_back: Number of days to analyze
        report_format: Output format
        
    Returns:
        Summary report data
    """
    try:
        logger.info(f"Generating summary report for last {days_back} days")
        
        # Get data
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        waste_data = get_waste_data_for_period(start_date, end_date)
        
        if waste_data.empty:
            return create_empty_report("No data available for summary report")
        
        # Generate comprehensive summary
        report = {
            'metadata': {
                'report_type': 'Executive Summary Report',
                'period': f"Last {days_back} days",
                'generated_at': datetime.utcnow(),
                'total_records': len(waste_data)
            },
            'executive_summary': generate_executive_summary(waste_data),
            'key_metrics': generate_key_metrics(waste_data),
            'trend_analysis': generate_summary_trend_analysis(waste_data),
            'top_insights': generate_top_insights(waste_data),
            'action_items': generate_action_items(waste_data)
        }
        
        # Format output
        if report_format == 'dataframe':
            return format_report_as_dataframe(report)
        elif report_format == 'dict':
            return report
        elif report_format == 'html':
            return format_report_as_html(report)
        else:
            return report
        
    except Exception as e:
        logger.error(f"Error generating summary report: {e}")
        return create_error_report("Failed to generate summary report")


# Report section generators

def generate_waste_summary(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate waste summary statistics."""
    try:
        total_waste = waste_data['quantity_kg'].sum()
        avg_daily = total_waste / len(waste_data['date'].unique())
        
        return {
            'total_waste_kg': total_waste,
            'average_daily_waste_kg': avg_daily,
            'total_records': len(waste_data),
            'unique_days': len(waste_data['date'].unique()),
            'peak_waste_day': waste_data.groupby('date')['quantity_kg'].sum().idxmax(),
            'lowest_waste_day': waste_data.groupby('date')['quantity_kg'].sum().idxmin(),
            'formatted': {
                'total_waste': format_weight(total_waste),
                'average_daily_waste': format_weight(avg_daily)
            }
        }
    except Exception as e:
        logger.error(f"Error generating waste summary: {e}")
        return {}


def generate_category_analysis(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate category analysis."""
    try:
        category_stats = waste_data.groupby('category').agg({
            'quantity_kg': ['sum', 'mean', 'count'],
            'estimated_cost': 'sum'
        }).round(2)
        
        analysis = {}
        for category in category_stats.index:
            analysis[category] = {
                'total_kg': float(category_stats.loc[category, ('quantity_kg', 'sum')]),
                'avg_kg': float(category_stats.loc[category, ('quantity_kg', 'mean')]),
                'count': int(category_stats.loc[category, ('quantity_kg', 'count')]),
                'total_cost': float(category_stats.loc[category, ('estimated_cost', 'sum')]),
                'percentage': (float(category_stats.loc[category, ('quantity_kg', 'sum')]) / waste_data['quantity_kg'].sum()) * 100
            }
        
        return analysis
    except Exception as e:
        logger.error(f"Error generating category analysis: {e}")
        return {}


def generate_source_analysis(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate source analysis."""
    try:
        source_stats = waste_data.groupby('source').agg({
            'quantity_kg': ['sum', 'mean', 'count'],
            'estimated_cost': 'sum'
        }).round(2)
        
        analysis = {}
        for source in source_stats.index:
            analysis[source] = {
                'total_kg': float(source_stats.loc[source, ('quantity_kg', 'sum')]),
                'avg_kg': float(source_stats.loc[source, ('quantity_kg', 'mean')]),
                'count': int(source_stats.loc[source, ('quantity_kg', 'count')]),
                'total_cost': float(source_stats.loc[source, ('estimated_cost', 'sum')]),
                'percentage': (float(source_stats.loc[source, ('quantity_kg', 'sum')]) / waste_data['quantity_kg'].sum()) * 100
            }
        
        return analysis
    except Exception as e:
        logger.error(f"Error generating source analysis: {e}")
        return {}


def generate_temporal_analysis(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate temporal analysis."""
    try:
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        waste_data['day_of_week'] = waste_data['date'].dt.dayofweek
        waste_data['month'] = waste_data['date'].dt.month
        
        # Daily patterns
        daily_avg = waste_data.groupby('date')['quantity_kg'].sum()
        
        # Day of week patterns
        dow_avg = waste_data.groupby('day_of_week')['quantity_kg'].mean()
        
        # Monthly patterns (if data available)
        monthly_avg = waste_data.groupby('month')['quantity_kg'].mean()
        
        return {
            'daily_statistics': {
                'average': daily_avg.mean(),
                'maximum': daily_avg.max(),
                'minimum': daily_avg.min(),
                'standard_deviation': daily_avg.std()
            },
            'day_of_week_patterns': dow_avg.to_dict(),
            'monthly_patterns': monthly_avg.to_dict() if len(monthly_avg) > 1 else {},
            'trend': calculate_simple_trend(daily_avg)
        }
    except Exception as e:
        logger.error(f"Error generating temporal analysis: {e}")
        return {}


def generate_cost_summary(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate cost summary."""
    try:
        total_cost = waste_data['estimated_cost'].sum()
        total_waste = waste_data['quantity_kg'].sum()
        avg_cost_per_kg = total_cost / total_waste if total_waste > 0 else 0
        
        return {
            'total_cost': total_cost,
            'average_cost_per_kg': avg_cost_per_kg,
            'daily_average_cost': total_cost / len(waste_data['date'].unique()),
            'formatted': {
                'total_cost': format_currency(total_cost),
                'average_cost_per_kg': format_currency(avg_cost_per_kg),
                'daily_average_cost': format_currency(total_cost / len(waste_data['date'].unique()))
            }
        }
    except Exception as e:
        logger.error(f"Error generating cost summary: {e}")
        return {}


def generate_cost_by_category(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate cost analysis by category."""
    try:
        category_cost = waste_data.groupby('category')['estimated_cost'].sum()
        
        analysis = {}
        for category in category_cost.index:
            category_data = waste_data[waste_data['category'] == category]
            analysis[category] = {
                'total_cost': float(category_cost[category]),
                'average_cost_per_kg': float(category_cost[category] / category_data['quantity_kg'].sum()),
                'percentage': (float(category_cost[category]) / waste_data['estimated_cost'].sum()) * 100
            }
        
        return analysis
    except Exception as e:
        logger.error(f"Error generating cost by category: {e}")
        return {}


def generate_cost_trends(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate cost trends."""
    try:
        waste_data['date'] = pd.to_datetime(waste_data['date'])
        daily_cost = waste_data.groupby('date')['estimated_cost'].sum()
        
        return {
            'trend': calculate_simple_trend(daily_cost),
            'volatility': daily_cost.std() / daily_cost.mean() if daily_cost.mean() > 0 else 0,
            'peak_cost_day': daily_cost.idxmax(),
            'lowest_cost_day': daily_cost.idxmin()
        }
    except Exception as e:
        logger.error(f"Error generating cost trends: {e}")
        return {}


def generate_cost_efficiency(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate cost efficiency metrics."""
    try:
        total_cost = waste_data['estimated_cost'].sum()
        total_waste = waste_data['quantity_kg'].sum()
        
        # Efficiency score based on cost per kg
        avg_cost_per_kg = total_cost / total_waste if total_waste > 0 else 0
        
        efficiency_score = 100
        if avg_cost_per_kg > 10:
            efficiency_score = 40
        elif avg_cost_per_kg > 5:
            efficiency_score = 60
        elif avg_cost_per_kg > 3:
            efficiency_score = 80
        
        return {
            'efficiency_score': efficiency_score,
            'cost_per_kg': avg_cost_per_kg,
            'efficiency_rating': 'High' if efficiency_score > 80 else 'Medium' if efficiency_score > 60 else 'Low'
        }
    except Exception as e:
        logger.error(f"Error generating cost efficiency: {e}")
        return {}


def generate_cost_recommendations(waste_data: pd.DataFrame) -> List[str]:
    """Generate cost-based recommendations."""
    try:
        recommendations = []
        
        total_cost = waste_data['estimated_cost'].sum()
        if total_cost > 5000:
            recommendations.append("High total waste cost indicates need for comprehensive cost reduction program")
        
        avg_cost_per_kg = total_cost / waste_data['quantity_kg'].sum()
        if avg_cost_per_kg > 10:
            recommendations.append("Focus on reducing waste of high-cost items")
        
        # Category-specific recommendations
        category_cost = waste_data.groupby('category')['estimated_cost'].sum()
        top_cost_category = category_cost.idxmax()
        
        if category_cost.max() / total_cost > 0.4:
            recommendations.append(f"Target {top_cost_category} category for immediate cost reduction")
        
        return recommendations
    except Exception as e:
        logger.error(f"Error generating cost recommendations: {e}")
        return []


def generate_efficiency_metrics(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate efficiency metrics."""
    try:
        total_waste = waste_data['quantity_kg'].sum()
        days = len(waste_data['date'].unique())
        avg_daily = total_waste / days
        
        # Consistency score
        daily_waste = waste_data.groupby('date')['quantity_kg'].sum()
        cv = daily_waste.std() / daily_waste.mean() if daily_waste.mean() > 0 else 0
        
        # Efficiency score
        efficiency_score = 100
        if avg_daily > 50:
            efficiency_score = 40
        elif avg_daily > 25:
            efficiency_score = 60
        elif avg_daily > 10:
            efficiency_score = 80
        
        return {
            'overall_efficiency': efficiency_score,
            'daily_average_waste': avg_daily,
            'consistency_score': max(0, 100 - cv * 100),
            'efficiency_rating': 'High' if efficiency_score > 80 else 'Medium' if efficiency_score > 60 else 'Low'
        }
    except Exception as e:
        logger.error(f"Error generating efficiency metrics: {e}")
        return {}


def generate_performance_analysis(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate performance analysis."""
    try:
        daily_waste = waste_data.groupby('date')['quantity_kg'].sum()
        
        return {
            'performance_trend': calculate_simple_trend(daily_waste),
            'peak_performance_day': daily_waste.idxmin(),
            'worst_performance_day': daily_waste.idxmax(),
            'performance_variance': daily_waste.var(),
            'improvement_potential': (daily_waste.max() - daily_waste.min()) * 0.3
        }
    except Exception as e:
        logger.error(f"Error generating performance analysis: {e}")
        return {}


def generate_benchmarking(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate benchmarking analysis."""
    try:
        avg_daily_waste = waste_data.groupby('date')['quantity_kg'].sum().mean()
        
        # Industry benchmarks (simplified)
        benchmarks = {
            'excellent': 10,  # kg per day
            'good': 25,
            'average': 50,
            'poor': 100
        }
        
        current_level = 'poor'
        for level, threshold in benchmarks.items():
            if avg_daily_waste <= threshold:
                current_level = level
                break
        
        return {
            'current_level': current_level,
            'benchmark_comparison': benchmarks,
            'improvement_needed': avg_daily_waste - benchmarks['good'],
            'target_level': 'good'
        }
    except Exception as e:
        logger.error(f"Error generating benchmarking: {e}")
        return {}


def generate_improvement_opportunities(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate improvement opportunities."""
    try:
        opportunities = []
        
        # Category-based opportunities
        category_stats = waste_data.groupby('category')['quantity_kg'].sum()
        for category, amount in category_stats.items():
            if amount > category_stats.sum() * 0.3:  # More than 30% of total
                opportunities.append({
                    'area': category,
                    'potential_reduction': amount * 0.3,  # 30% reduction potential
                    'priority': 'high' if amount > category_stats.sum() * 0.4 else 'medium'
                })
        
        return opportunities
    except Exception as e:
        logger.error(f"Error generating improvement opportunities: {e}")
        return []


# Helper functions

def get_waste_data_for_period(start_date: date, end_date: date) -> pd.DataFrame:
    """Get waste data for specified period."""
    try:
        db = get_session()
        
        records = db.query(WasteRecord).filter(
            WasteRecord.date >= start_date,
            WasteRecord.date <= end_date,
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


def get_forecast_data(days_ahead: int, model_type: str) -> List[Dict]:
    """Get forecast data."""
    try:
        # This would integrate with the forecasting module
        # For now, return mock data
        forecast_data = []
        
        for i in range(days_ahead):
            future_date = date.today() + timedelta(days=i+1)
            forecast_data.append({
                'date': future_date,
                'predicted_value': np.random.normal(30, 5),  # Mock prediction
                'confidence_score': np.random.uniform(0.7, 0.9),
                'model_type': model_type
            })
        
        return forecast_data
    except Exception as e:
        logger.error(f"Error getting forecast data: {e}")
        return []


def calculate_simple_trend(series: pd.Series) -> str:
    """Calculate simple trend."""
    try:
        if len(series) < 2:
            return 'insufficient_data'
        
        x = np.arange(len(series))
        y = series.values
        
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    except Exception as e:
        logger.error(f"Error calculating trend: {e}")
        return 'unknown'


def format_report_as_dataframe(report: Dict[str, Any]) -> pd.DataFrame:
    """Format report as DataFrame."""
    try:
        # Create a summary DataFrame
        summary_data = []
        
        if 'summary' in report:
            summary = report['summary']
            summary_data.append(['Total Waste (kg)', summary.get('total_waste_kg', 0)])
            summary_data.append(['Average Daily Waste (kg)', summary.get('average_daily_waste_kg', 0)])
            summary_data.append(['Total Records', summary.get('total_records', 0)])
        
        df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        return df
    except Exception as e:
        logger.error(f"Error formatting report as DataFrame: {e}")
        return pd.DataFrame()


def format_report_as_html(report: Dict[str, Any]) -> str:
    """Format report as HTML."""
    try:
        html = f"<html><body>"
        html += f"<h1>{report['metadata']['report_type']}</h1>"
        html += f"<p>Period: {report['metadata']['period']}</p>"
        html += f"<p>Generated: {report['metadata']['generated_at']}</p>"
        
        if 'summary' in report:
            html += "<h2>Summary</h2>"
            for key, value in report['summary'].items():
                html += f"<p><strong>{key}:</strong> {value}</p>"
        
        html += "</body></html>"
        return html
    except Exception as e:
        logger.error(f"Error formatting report as HTML: {e}")
        return "<html><body>Error generating report</body></html>"


def create_empty_report(message: str) -> Dict[str, Any]:
    """Create empty report."""
    return {
        'metadata': {
            'report_type': 'Empty Report',
            'generated_at': datetime.utcnow(),
            'message': message
        },
        'summary': {},
        'data': []
    }


def create_error_report(message: str) -> Dict[str, Any]:
    """Create error report."""
    return {
        'metadata': {
            'report_type': 'Error Report',
            'generated_at': datetime.utcnow(),
            'error': message
        },
        'summary': {},
        'data': []
    }


# Placeholder functions for remaining report types
def generate_confidence_analysis(forecast_data: List[Dict]) -> Dict[str, Any]:
    """Generate confidence analysis for forecasts."""
    return {}


def generate_forecast_trend_analysis(forecast_data: List[Dict]) -> Dict[str, Any]:
    """Generate forecast trend analysis."""
    return {}


def generate_forecast_recommendations(forecast_data: List[Dict]) -> List[str]:
    """Generate forecast-based recommendations."""
    return []


def generate_forecast_summary(forecast_data: List[Dict]) -> Dict[str, Any]:
    """Generate forecast summary."""
    return {}


def generate_executive_summary(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate executive summary."""
    return {}


def generate_key_metrics(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate key metrics."""
    return {}


def generate_summary_trend_analysis(waste_data: pd.DataFrame) -> Dict[str, Any]:
    """Generate summary trend analysis."""
    return {}


def generate_top_insights(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate top insights."""
    return []


def generate_action_items(waste_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate action items."""
    return []
