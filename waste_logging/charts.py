"""
Plotly charts for Food Waste Logging module.

This module provides comprehensive data visualization charts
for waste analysis, trends, and insights.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging

from database.models import FoodWasteLog, WasteCategory, MealType
from waste_logging.helpers import WasteLoggingHelpers

logger = logging.getLogger(__name__)


class WasteLoggingCharts:
    """Chart creation for waste logging data visualization."""
    
    @staticmethod
    def create_waste_trend_chart(waste_logs: List[FoodWasteLog], days: int = 30) -> go.Figure:
        """Create waste trend chart over time."""
        if not waste_logs:
            # Empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Waste Trend", height=400)
            return fig
        
        # Group by date
        daily_waste = {}
        for log in waste_logs:
            date_str = log.waste_date.isoformat()
            if date_str not in daily_waste:
                daily_waste[date_str] = 0
            daily_waste[date_str] += log.quantity_kg
        
        # Create date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        # Fill missing dates with zero
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            if date_str not in daily_waste:
                daily_waste[date_str] = 0
            current_date += timedelta(days=1)
        
        # Sort dates
        sorted_dates = sorted(daily_waste.keys())
        waste_values = [daily_waste[date] for date in sorted_dates]
        
        # Create chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=sorted_dates,
            y=waste_values,
            mode='lines+markers',
            name='Daily Waste',
            line=dict(color='#FF6B6B', width=3),
            marker=dict(size=6, color='#FF6B6B'),
            fill='tonexty',
            fillcolor='rgba(255, 107, 107, 0.2)'
        ))
        
        # Add trend line
        if len(waste_values) > 1:
            z = np.polyfit(range(len(waste_values)), waste_values, 1)
            p = np.poly1d(z)
            trend_line = p(range(len(waste_values)))
            
            fig.add_trace(go.Scatter(
                x=sorted_dates,
                y=trend_line,
                mode='lines',
                name='Trend',
                line=dict(color='#2E8B57', width=2, dash='dash'),
                showlegend=True
            ))
        
        fig.update_layout(
            title="Daily Waste Trend",
            xaxis_title="Date",
            yaxis_title="Waste (kg)",
            height=400,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_category_pie_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create pie chart for waste categories."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Waste by Category", height=400)
            return fig
        
        # Group by category
        category_totals = {}
        for log in waste_logs:
            if log.category not in category_totals:
                category_totals[log.category] = 0
            category_totals[log.category] += log.quantity_kg
        
        # Sort by quantity
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        fig = go.Figure(data=[go.Pie(
            labels=[cat[0] for cat in sorted_categories],
            values=[cat[1] for cat in sorted_categories],
            hole=0.3,
            marker_colors=[WasteLoggingHelpers.get_waste_category_color(cat[0]) for cat in sorted_categories],
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Quantity: %{value:.2f} kg<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Waste by Food Category",
            height=400,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_waste_type_bar_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create bar chart for waste types."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Waste by Type", height=400)
            return fig
        
        # Group by waste category
        waste_type_totals = {}
        for log in waste_logs:
            waste_type = log.waste_category.value
            if waste_type not in waste_type_totals:
                waste_type_totals[waste_type] = 0
            waste_type_totals[waste_type] += log.quantity_kg
        
        # Sort by quantity
        sorted_types = sorted(waste_type_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=[type[0].replace('_', ' ').title() for type in sorted_types],
            y=[type[1] for type in sorted_types],
            marker_color=[WasteLoggingHelpers.get_waste_category_color(type[0]) for type in sorted_types],
            text=[f"{type[1]:.1f} kg" for type in sorted_types],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Quantity: %{y:.2f} kg<extra></extra>'
        )])
        
        fig.update_layout(
            title="Waste by Type",
            xaxis_title="Waste Type",
            yaxis_title="Quantity (kg)",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_dining_hall_comparison(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create comparison chart for dining halls."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Dining Hall Comparison", height=400)
            return fig
        
        # Group by dining hall
        hall_totals = {}
        for log in waste_logs:
            if log.dining_hall not in hall_totals:
                hall_totals[log.dining_hall] = 0
            hall_totals[log.dining_hall] += log.quantity_kg
        
        # Sort by quantity
        sorted_halls = sorted(hall_totals.items(), key=lambda x: x[1], reverse=True)
        
        fig = go.Figure(data=[go.Bar(
            x=[hall[0] for hall in sorted_halls],
            y=[hall[1] for hall in sorted_halls],
            marker_color='#4ECDC4',
            text=[f"{hall[1]:.1f} kg" for hall in sorted_halls],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Total Waste: %{y:.2f} kg<extra></extra>'
        )])
        
        fig.update_layout(
            title="Total Waste by Dining Hall",
            xaxis_title="Dining Hall",
            yaxis_title="Total Waste (kg)",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_top_waste_items_chart(waste_logs: List[FoodWasteLog], limit: int = 10) -> go.Figure:
        """Create chart for top waste items."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Top Waste Items", height=400)
            return fig
        
        # Group by food item
        item_totals = {}
        for log in waste_logs:
            if log.food_item not in item_totals:
                item_totals[log.food_item] = 0
            item_totals[log.food_item] += log.quantity_kg
        
        # Sort and limit
        sorted_items = sorted(item_totals.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=[item[1] for item in sorted_items],
            y=[item[0] for item in sorted_items],
            orientation='h',
            marker_color='#FF6B6B',
            hovertemplate='<b>%{y}</b><br>Quantity: %{x:.2f} kg<extra></extra>'
        )])
        
        fig.update_layout(
            title=f"Top {limit} Waste Items",
            xaxis_title="Quantity (kg)",
            yaxis_title="Food Item",
            height=max(400, limit * 40),
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_cost_analysis_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create cost analysis chart."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Cost Analysis", height=400)
            return fig
        
        # Group by category with cost
        category_costs = {}
        for log in waste_logs:
            if log.category not in category_costs:
                category_costs[log.category] = {'quantity': 0, 'cost': 0}
            category_costs[log.category]['quantity'] += log.quantity_kg
            category_costs[log.category]['cost'] += log.estimated_cost or 0
        
        # Sort by cost
        sorted_categories = sorted(category_costs.items(), key=lambda x: x[1]['cost'], reverse=True)
        
        # Create dual-axis chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add cost bars
        fig.add_trace(
            go.Bar(
                x=[cat[0] for cat in sorted_categories],
                y=[cat[1]['cost'] for cat in sorted_categories],
                name='Cost ($)',
                marker_color='#FFA500',
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
            ),
            secondary_y=False
        )
        
        # Add quantity line
        fig.add_trace(
            go.Scatter(
                x=[cat[0] for cat in sorted_categories],
                y=[cat[1]['quantity'] for cat in sorted_categories],
                mode='lines+markers',
                name='Quantity (kg)',
                line=dict(color='#2E8B57', width=3),
                marker=dict(size=8, color='#2E8B57'),
                hovertemplate='<b>%{x}</b><br>Quantity: %{y:.2f} kg<extra></extra>'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Cost Analysis by Category",
            xaxis_title="Category",
            height=400,
            template='plotly_white'
        )
        
        fig.update_yaxes(title_text="Cost ($)", secondary_y=False)
        fig.update_yaxes(title_text="Quantity (kg)", secondary_y=True)
        
        return fig
    
    @staticmethod
    def create_environmental_impact_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create environmental impact chart."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Environmental Impact", height=400)
            return fig
        
        # Calculate environmental impact
        total_impact = {'co2_kg': 0, 'water_liters': 0, 'land_m2': 0}
        
        for log in waste_logs:
            impact = WasteLoggingHelpers.calculate_environmental_impact(
                log.category, log.quantity_kg
            )
            total_impact['co2_kg'] += impact['co2_kg']
            total_impact['water_liters'] += impact['water_liters']
            total_impact['land_m2'] += impact['land_m2']
        
        # Create chart
        metrics = ['CO₂ Impact (kg)', 'Water Footprint (L)', 'Land Use (m²)']
        values = [total_impact['co2_kg'], total_impact['water_liters'], total_impact['land_m2']]
        colors = ['#DC3545', '#007BFF', '#28A745']
        
        fig = go.Figure(data=[go.Bar(
            x=metrics,
            y=values,
            marker_color=colors,
            text=[f"{val:,.0f}" for val in values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>'
        )])
        
        fig.update_layout(
            title="Environmental Impact",
            xaxis_title="Impact Metric",
            yaxis_title="Value",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_meal_period_comparison(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create meal period comparison chart."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Meal Period Comparison", height=400)
            return fig
        
        # Group by meal period
        period_totals = {}
        for log in waste_logs:
            period = log.meal_period.value if log.meal_period else 'Unknown'
            if period not in period_totals:
                period_totals[period] = 0
            period_totals[period] += log.quantity_kg
        
        # Sort by meal type order
        meal_order = ['breakfast', 'lunch', 'dinner', 'snack']
        sorted_periods = []
        
        for meal in meal_order:
            if meal in period_totals:
                sorted_periods.append((meal, period_totals[meal]))
        
        # Add any remaining periods
        for period, total in period_totals.items():
            if period not in meal_order:
                sorted_periods.append((period, total))
        
        # Create chart with emojis
        period_emojis = {
            'breakfast': '🍳',
            'lunch': '🍽️',
            'dinner': '🍽️',
            'snack': '🍪'
        }
        
        labels = [f"{period_emojis.get(period, '📦')} {period.title()}" for period, _ in sorted_periods]
        values = [total for _, total in sorted_periods]
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color='#95E1D3',
            text=[f"{total:.1f} kg" for total in values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Quantity: %{y:.2f} kg<extra></extra>'
        )])
        
        fig.update_layout(
            title="Waste by Meal Period",
            xaxis_title="Meal Period",
            yaxis_title="Quantity (kg)",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_waste_heatmap(waste_logs: List[FoodWasteLog]) -> go.Figure:
        """Create waste heatmap by day and category."""
        if not waste_logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Waste Heatmap", height=400)
            return fig
        
        # Create pivot table
        df = WasteLoggingHelpers.create_waste_dataframe(waste_logs)
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title="Waste Heatmap", height=400)
            return fig
        
        # Extract day of week
        df['day_of_week'] = pd.to_datetime(df['waste_date']).dt.day_name()
        
        # Create pivot table
        pivot_table = df.pivot_table(
            values='quantity_kg',
            index='day_of_week',
            columns='category',
            aggfunc='sum',
            fill_value=0
        )
        
        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot_table = pivot_table.reindex(day_order, fill_value=0)
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot_table.values,
            x=pivot_table.columns,
            y=pivot_table.index,
            colorscale='Reds',
            hovertemplate='<b>%{y}</b><br>%{x}<br>Waste: %{z:.2f} kg<extra></extra>',
            text=pivot_table.values,
            texttemplate="%{text:.1f}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title="Waste Heatmap by Day and Category",
            xaxis_title="Food Category",
            yaxis_title="Day of Week",
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_waste_score_gauge(score: float, grade: str) -> go.Figure:
        """Create waste performance score gauge."""
        # Determine color based on grade
        grade_colors = {
            'A': '#28A745',
            'B': '#20C997',
            'C': '#FFC107',
            'D': '#FD7E14',
            'F': '#DC3545'
        }
        
        color = grade_colors.get(grade, '#6C757D')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Waste Performance Score: {grade}"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 60], 'color': "lightgray"},
                    {'range': [60, 80], 'color': "gray"},
                    {'range': [80, 100], 'color': color}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_waste_forecast_chart(historical_data: List[Dict], forecast_data: List[Dict]) -> go.Figure:
        """Create waste forecast chart with historical data and predictions."""
        fig = go.Figure()
        
        # Add historical data
        if historical_data:
            historical_dates = [item['date'] for item in historical_data]
            historical_values = [item['waste_kg'] for item in historical_data]
            
            fig.add_trace(go.Scatter(
                x=historical_dates,
                y=historical_values,
                mode='lines+markers',
                name='Historical',
                line=dict(color='#FF6B6B', width=2),
                marker=dict(size=6, color='#FF6B6B')
            ))
        
        # Add forecast data
        if forecast_data:
            forecast_dates = [item['date'] for item in forecast_data]
            forecast_values = [item['predicted_waste'] for item in forecast_data]
            forecast_upper = [item.get('upper_bound', item['predicted_waste']) for item in forecast_data]
            forecast_lower = [item.get('lower_bound', item['predicted_waste']) for item in forecast_data]
            
            # Add confidence interval
            fig.add_trace(go.Scatter(
                x=forecast_dates + forecast_dates[::-1],
                y=forecast_upper + forecast_lower[::-1],
                fill='toself',
                fillcolor='rgba(46, 139, 87, 0.2)',
                line=dict(color='rgba(46, 139, 87, 0)'),
                name='Confidence Interval',
                hoverinfo="skip",
                showlegend=True
            ))
            
            # Add forecast line
            fig.add_trace(go.Scatter(
                x=forecast_dates,
                y=forecast_values,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#2E8B57', width=2, dash='dash'),
                marker=dict(size=6, color='#2E8B57')
            ))
        
        fig.update_layout(
            title="Waste Forecast",
            xaxis_title="Date",
            yaxis_title="Waste (kg)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_waste_comparison_chart(current_period: List[FoodWasteLog], 
                                   previous_period: List[FoodWasteLog]) -> go.Figure:
        """Create comparison chart between current and previous periods."""
        # Calculate totals for each period
        current_total = sum(log.quantity_kg for log in current_period) if current_period else 0
        previous_total = sum(log.quantity_kg for log in previous_period) if previous_period else 0
        
        # Calculate percentage change
        if previous_total > 0:
            change_percentage = ((current_total - previous_total) / previous_total) * 100
        else:
            change_percentage = 0
        
        fig = go.Figure(data=[
            go.Bar(
                name='Current Period',
                x=['Current Period'],
                y=[current_total],
                marker_color='#FF6B6B',
                text=[f"{current_total:.1f} kg"],
                textposition='outside'
            ),
            go.Bar(
                name='Previous Period',
                x=['Previous Period'],
                y=[previous_total],
                marker_color='#95E1D3',
                text=[f"{previous_total:.1f} kg"],
                textposition='outside'
            )
        ])
        
        fig.update_layout(
            title=f"Period Comparison (Change: {change_percentage:+.1f}%)",
            yaxis_title="Waste (kg)",
            height=300,
            template='plotly_white'
        )
        
        return fig


# Convenience functions for direct use
def create_waste_trend_chart(waste_logs: List[FoodWasteLog], days: int = 30) -> go.Figure:
    """Create waste trend chart over time."""
    return WasteLoggingCharts.create_waste_trend_chart(waste_logs, days)


def create_category_pie_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
    """Create pie chart for waste categories."""
    return WasteLoggingCharts.create_category_pie_chart(waste_logs)


def create_waste_type_bar_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
    """Create bar chart for waste types."""
    return WasteLoggingCharts.create_waste_type_bar_chart(waste_logs)


def create_dining_hall_comparison(waste_logs: List[FoodWasteLog]) -> go.Figure:
    """Create comparison chart for dining halls."""
    return WasteLoggingCharts.create_dining_hall_comparison(waste_logs)


def create_top_waste_items_chart(waste_logs: List[FoodWasteLog], limit: int = 10) -> go.Figure:
    """Create chart for top waste items."""
    return WasteLoggingCharts.create_top_waste_items_chart(waste_logs, limit)


def create_cost_analysis_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
    """Create cost analysis chart."""
    return WasteLoggingCharts.create_cost_analysis_chart(waste_logs)


def create_environmental_impact_chart(waste_logs: List[FoodWasteLog]) -> go.Figure:
    """Create environmental impact chart."""
    return WasteLoggingCharts.create_environmental_impact_chart(waste_logs)
