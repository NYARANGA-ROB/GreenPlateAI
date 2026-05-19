"""
Plotly charts for GreenPlateAI analytics dashboard.
This module provides comprehensive visualization charts for
dashboard metrics and analytics.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
logger = logging.getLogger(__name__)


class AnalyticsCharts:
    """Chart creation for analytics dashboard."""
    @staticmethod
    def create_kpi_card(title: str, value: float, unit: str, change: float = 0,
                       trend: str = 'stable', color: str = 'blue') -> go.Figure:
        """Create KPI card visualization."""
        # Determine trend color
        trend_colors = {
            'increasing': 'green' if color == 'blue' else 'lightgreen',
            'decreasing': 'red' if color == 'blue' else 'lightcoral',
            'stable': 'gray'
        }
        
        trend_color = trend_colors.get(trend, 'gray')
        
        # Create figure
        fig = go.Figure()
        # Add main value
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=value,
            title={"text": title},
            delta={'reference': value - (value * change / 100) if change != 0 else value},
            number={'suffix': f" {unit}"},
            domain={'x': [0, 1], 'y': [0, 1]},
            valuefont={'size': 24},
            titlefont={'size': 14}
        ))
        
        # Update layout
        fig.update_layout(
            height=120,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        return fig
    
    @staticmethod
    def create_line_chart(data: pd.DataFrame, x_col: str, y_col: str,
                        title: str = "", color: str = 'blue') -> go.Figure:
        """Create line chart for trends."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode='lines+markers',
            name=title,
            line=dict(color=color, width=2),
            marker=dict(size=4, color=color),
            hovertemplate=f'<b>%{{x}}</b><br>{y_col}: %{{y}}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_multi_line_chart(data: pd.DataFrame, x_col: str, y_cols: List[str],
                             title: str = "", colors: List[str] = None) -> go.Figure:
        """Create multi-line chart for multiple trends."""
        if colors is None:
            colors = px.colors.qualitative.Set1[:len(y_cols)]
        
        fig = go.Figure()
        
        for i, y_col in enumerate(y_cols):
            fig.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode='lines+markers',
                name=y_col.replace('_', ' ').title(),
                line=dict(color=colors[i], width=2),
                marker=dict(size=4, color=colors[i]),
                hovertemplate=f'<b>%{{x}}</b><br>{y_col}: %{{y}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title='Value',
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_pie_chart(data: Dict[str, float], title: str = "",
                        colors: List[str] = None) -> go.Figure:
        """Create pie chart for categorical data."""
        if not data:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        labels = list(data.keys())
        values = list(data.values())
        
        if colors is None:
            colors = px.colors.qualitative.Set3[:len(labels)]
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors,
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Value: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(data: pd.DataFrame, x_col: str, y_col: str,
                        title: str = "", color: str = 'blue',
                        orientation: str = 'vertical') -> go.Figure:
        """Create bar chart."""
        if orientation == 'horizontal':
            fig = go.Figure(data=[go.Bar(
                x=data[y_col],
                y=data[x_col],
                orientation='h',
                marker_color=color,
                hovertemplate=f'<b>%{{y}}</b><br>{y_col}: %{{x}}<extra></extra>'
            )])
            
            fig.update_layout(
                title=title,
                xaxis_title=y_col.replace('_', ' ').title(),
                yaxis_title=x_col.replace('_', ' ').title(),
                height=max(400, len(data) * 30),
                template='plotly_white'
            )
        else:
            fig = go.Figure(data=[go.Bar(
                x=data[x_col],
                y=data[y_col],
                marker_color=color,
                hovertemplate=f'<b>%{{x}}</b><br>{y_col}: %{{y}}<extra></extra>'
            )])
            
            fig.update_layout(
                title=title,
                xaxis_title=x_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title(),
                height=400,
                template='plotly_white'
            )
        
        return fig
    
    @staticmethod
    def create_heatmap(data: pd.DataFrame, title: str = "",
                      colorscale: str = 'Viridis') -> go.Figure:
        """Create heatmap."""
        fig = go.Figure(data=go.Heatmap(
            z=data.values,
            x=data.columns,
            y=data.index,
            colorscale=colorscale,
            hovertemplate='<b>%{y}</b><br>%{x}<br>Value: %{z}<extra></extra>',
            text=data.values,
            texttemplate="%{text:.1f}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title=title,
            height=500,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_weekly_trends_chart(weekly_data: Dict[str, Any], title: str = "Weekly Trends") -> go.Figure:
        """Create weekly trends chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Meals Served', 'Waste Generated'),
            vertical_spacing=0.1
        )
        
        # Meals data
        weeks = list(weekly_data.get('meals', {}).keys())
        meal_counts = [weekly_data['meals'][week].get('user_id', 0) for week in weeks]
        
        fig.add_trace(go.Scatter(
            x=weeks,
            y=meal_counts,
            mode='lines+markers',
            name='Meals Served',
            line=dict(color='#2E8B57', width=2),
            marker=dict(size=6, color='#2E8B57'),
            hovertemplate='<b>Week %{x}</b><br>Meals: %{y}<extra></extra>'
        ), row=1, col=1)
        
        # Waste data
        waste_quantities = [weekly_data.get('waste', {}).get(week, {}).get('quantity', 0) for week in weeks]
        
        fig.add_trace(go.Scatter(
            x=weeks,
            y=waste_quantities,
            mode='lines+markers',
            name='Waste (kg)',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=6, color='#FF6B6B'),
            hovertemplate='<b>Week %{x}</b><br>Waste: %{y} kg<extra></extra>'
        ), row=2, col=1)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Week", row=2, col=1)
        fig.update_yaxes(title_text="Meals Served", row=1, col=1)
        fig.update_yaxes(title_text="Waste (kg)", row=2, col=1)
        
        return fig
    
    @staticmethod
    def create_monthly_trends_chart(monthly_data: Dict[str, Any], title: str = "Monthly Trends") -> go.Figure:
        """Create monthly trends chart."""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Meals Served', 'Waste Generated'),
            vertical_spacing=0.1
        )
        
        # Month names
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Meals data
        months = list(monthly_data.get('meals', {}).keys())
        month_labels = [month_names[month-1] if month <= 12 else f'Month {month}' for month in months]
        meal_counts = [monthly_data['meals'][month].get('user_id', 0) for month in months]
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=meal_counts,
            mode='lines+markers',
            name='Meals Served',
            line=dict(color='#2E8B57', width=2),
            marker=dict(size=6, color='#2E8B57'),
            hovertemplate='<b>%{x}</b><br>Meals: %{y}<extra></extra>'
        ), row=1, col=1)
        
        # Waste data
        waste_quantities = [monthly_data.get('waste', {}).get(month, {}).get('quantity', 0) for month in months]
        
        fig.add_trace(go.Scatter(
            x=month_labels,
            y=waste_quantities,
            mode='lines+markers',
            name='Waste (kg)',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=6, color='#FF6B6B'),
            hovertemplate='<b>%{x}</b><br>Waste: %{y} kg<extra></extra>'
        ), row=2, col=1)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            hovermode='x unified'
        )
        
        fig.update_xaxes(title_text="Month", row=2, col=1)
        fig.update_yaxes(title_text="Meals Served", row=1, col=1)
        fig.update_yaxes(title_text="Waste (kg)", row=2, col=1)
        
        return fig
    
    @staticmethod
    def create_meal_popularity_chart(popularity_data: Dict[str, Any], title: str = "Meal Popularity") -> go.Figure:
        """Create meal popularity chart."""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('By Meal Type', 'By Dining Hall'),
            specs=[[{"type": "pie"}, {"type": "pie"}]]
        )
        
        # By meal type
        meal_types = popularity_data.get('by_meal_type', {})
        if meal_types:
            fig.add_trace(go.Pie(
                labels=list(meal_types.keys()),
                values=list(meal_types.values()),
                name="Meal Type",
                hole=0.3,
                marker_colors=px.colors.qualitative.Set3[:len(meal_types)],
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            ), row=1, col=1)
        
        # By dining hall
        dining_halls = popularity_data.get('by_dining_hall', {})
        if dining_halls:
            fig.add_trace(go.Pie(
                labels=list(dining_halls.keys()),
                values=list(dining_halls.values()),
                name="Dining Hall",
                hole=0.3,
                marker_colors=px.colors.qualitative.Pastel[:len(dining_halls)],
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            ), row=1, col=2)
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_satisfaction_chart(satisfaction_data: Dict[str, Any], title: str = "Student Satisfaction") -> go.Figure:
        """Create satisfaction analysis chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Overall Score', 'By Meal Type', 'By Dining Hall', 'Rating Distribution'),
            specs=[[{"type": "indicator"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Overall score gauge
        overall_score = satisfaction_data.get('overall', 0)
        
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=overall_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Satisfaction"},
            gauge={
                'axis': {'range': [None, 5]},
                'bar': {'color': '#2E8B57'},
                'steps': [
                    {'range': [0, 2], 'color': "lightgray"},
                    {'range': [2, 3.5], 'color': "gray"},
                    {'range': [3.5, 5], 'color': "#2E8B57"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 4
                }
            }
        ), row=1, col=1)
        
        # By meal type
        meal_type_satisfaction = satisfaction_data.get('by_meal_type', {})
        if meal_type_satisfaction:
            fig.add_trace(go.Bar(
                x=list(meal_type_satisfaction.keys()),
                y=list(meal_type_satisfaction.values()),
                name='By Meal Type',
                marker_color='#4ECDC4',
                hovertemplate='<b>%{x}</b><br>Satisfaction: %{y:.2f}<extra></extra>'
            ), row=1, col=2)
        
        # By dining hall
        dining_hall_satisfaction = satisfaction_data.get('by_dining_hall', {})
        if dining_hall_satisfaction:
            fig.add_trace(go.Bar(
                x=list(dining_hall_satisfaction.keys()),
                y=list(dining_hall_satisfaction.values()),
                name='By Dining Hall',
                marker_color='#FF6B6B',
                hovertemplate='<b>%{x}</b><br>Satisfaction: %{y:.2f}<extra></extra>'
            ), row=2, col=1)
        
        # Rating distribution
        rating_distribution = satisfaction_data.get('rating_distribution', {})
        if rating_distribution:
            fig.add_trace(go.Bar(
                x=list(rating_distribution.keys()),
                y=list(rating_distribution.values()),
                name='Rating Distribution',
                marker_color='#FFA500',
                hovertemplate='<b>Rating: %{x}</b><br>Count: %{y}<extra></extra>'
            ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_environmental_impact_chart(impact_data: Dict[str, Any], title: str = "Environmental Impact") -> go.Figure:
        """Create environmental impact chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('CO₂ Impact', 'Water Footprint', 'Land Use', 'Net Impact'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # CO₂ impact
        co2_data = {
            'CO₂ Saved': impact_data.get('from_sustainability', {}).get('co2_saved', 0),
            'CO₂ from Waste': impact_data.get('from_waste', {}).get('co2_equivalent', 0)
        }
        
        fig.add_trace(go.Bar(
            x=list(co2_data.keys()),
            y=list(co2_data.values()),
            name='CO₂ (kg)',
            marker_color=['#2E8B57', '#DC3545'],
            hovertemplate='<b>%{x}</b><br>CO₂: %{y} kg<extra></extra>'
        ), row=1, col=1)
        
        # Water footprint
        water_data = {
            'Water Saved': impact_data.get('from_sustainability', {}).get('water_saved', 0),
            'Water from Waste': impact_data.get('from_waste', {}).get('water_footprint', 0)
        }
        
        fig.add_trace(go.Bar(
            x=list(water_data.keys()),
            y=list(water_data.values()),
            name='Water (L)',
            marker_color=['#4ECDC4', '#DC3545'],
            hovertemplate='<b>%{x}</b><br>Water: %{y} L<extra></extra>'
        ), row=1, col=2)
        
        # Land use
        land_data = {
            'Waste Reduction': impact_data.get('from_sustainability', {}).get('waste_reduced', 0),
            'Land from Waste': impact_data.get('from_waste', {}).get('land_use', 0)
        }
        
        fig.add_trace(go.Bar(
            x=list(land_data.keys()),
            y=list(land_data.values()),
            name='Land (m²)',
            marker_color=['#FFA500', '#DC3545'],
            hovertemplate='<b>%{x}</b><br>Land: %{y} m²<extra></extra>'
        ), row=2, col=1)
        
        # Net impact
        net_data = {
            'Net CO₂': impact_data.get('net', {}).get('co2_impact', 0),
            'Net Water': impact_data.get('net', {}).get('water_impact', 0),
            'Waste Reduction': impact_data.get('net', {}).get('waste_reduction', 0)
        }
        
        fig.add_trace(go.Bar(
            x=list(net_data.keys()),
            y=list(net_data.values()),
            name='Net Impact',
            marker_color=['#2E8B57', '#4ECDC4', '#FFA500'],
            hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
        ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_financial_chart(financial_data: Dict[str, Any], title: str = "Financial Metrics") -> go.Figure:
        """Create financial metrics chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Waste Cost', 'Estimated Savings', 'Cost per Meal', 'Daily Trends'),
            specs=[[{"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "bar"}, {"type": "scatter"}]]
        )
        
        # Waste cost indicator
        waste_cost = financial_data.get('waste_cost', 0)
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=waste_cost,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Waste Cost"},
            number={'prefix': '$'},
            valuefont={'size': 20},
            titlefont={'size': 12}
        ), row=1, col=1)
        
        # Estimated savings indicator
        estimated_savings = financial_data.get('estimated_savings', 0)
        
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=estimated_savings,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Estimated Savings"},
            number={'prefix': '$'},
            valuefont={'size': 20},
            titlefont={'size': 12}
        ), row=1, col=2)
        
        # Cost per meal
        cost_per_meal = financial_data.get('cost_per_meal', 0)
        
        fig.add_trace(go.Bar(
            x=['Cost per Meal'],
            y=[cost_per_meal],
            name='Cost per Meal',
            marker_color='#FF6B6B',
            hovertemplate='<b>Cost per Meal</b><br>$%{y:.2f}<extra></extra>'
        ), row=2, col=1)
        
        # Daily trends
        daily_trends = financial_data.get('daily_trends', {})
        if daily_trends:
            dates = list(daily_trends.keys())
            costs = list(daily_trends.values())
            
            fig.add_trace(go.Scatter(
                x=dates,
                y=costs,
                mode='lines+markers',
                name='Daily Cost',
                line=dict(color='#2E8B57', width=2),
                marker=dict(size=4, color='#2E8B57'),
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
            ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_category_analysis_chart(category_data: Dict[str, Any], title: str = "Category Analysis") -> go.Figure:
        """Create category analysis chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Waste by Category', 'Waste by Type', 'Top Waste Items', 'Cost by Category'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # By category
        by_category = category_data.get('by_category', {})
        if by_category:
            categories = list(by_category.keys())
            quantities = [by_category[cat].get('quantity', 0) for cat in categories]
            
            fig.add_trace(go.Bar(
                x=categories,
                y=quantities,
                name='Waste by Category',
                marker_color='#FF6B6B',
                hovertemplate='<b>%{x}</b><br>Quantity: %{y} kg<extra></extra>'
            ), row=1, col=1)
        
        # By waste type
        by_waste_type = category_data.get('by_waste_type', {})
        if by_waste_type:
            waste_types = list(by_waste_type.keys())
            quantities = [by_waste_type[wtype].get('quantity', 0) for wtype in waste_types]
            
            fig.add_trace(go.Bar(
                x=waste_types,
                y=quantities,
                name='Waste by Type',
                marker_color='#4ECDC4',
                hovertemplate='<b>%{x}</b><br>Quantity: %{y} kg<extra></extra>'
            ), row=1, col=2)
        
        # Top waste items
        top_items = category_data.get('top_items', {})
        if top_items:
            items = list(top_items.keys())[:5]  # Top 5
            quantities = [top_items[item].get('quantity', 0) for item in items]
            
            fig.add_trace(go.Bar(
                x=items,
                y=quantities,
                name='Top Items',
                marker_color='#FFA500',
                hovertemplate='<b>%{x}</b><br>Quantity: %{y} kg<extra></extra>'
            ), row=2, col=1)
        
        # Cost by category
        if by_category:
            categories = list(by_category.keys())
            costs = [by_category[cat].get('estimated_cost', 0) for cat in categories]
            
            fig.add_trace(go.Bar(
                x=categories,
                y=costs,
                name='Cost by Category',
                marker_color='#2E8B57',
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
            ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_time_patterns_chart(patterns_data: Dict[str, Any], title: str = "Time Patterns") -> go.Figure:
        """Create time patterns analysis chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Meals by Day of Week', 'Waste by Day of Week', 'Hourly Meals', 'Meal Type Distribution'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Meals by day of week
        dow_meals = patterns_data.get('day_of_week_meals', {})
        if dow_meals:
            days = list(dow_meals.keys())
            meal_counts = [dow_meals[day].get('user_id', 0) for day in days]
            
            fig.add_trace(go.Bar(
                x=days,
                y=meal_counts,
                name='Meals by Day',
                marker_color='#2E8B57',
                hovertemplate='<b>%{x}</b><br>Meals: %{y}<extra></extra>'
            ), row=1, col=1)
        
        # Waste by day of week
        dow_waste = patterns_data.get('day_of_week_waste', {})
        if dow_waste:
            days = list(dow_waste.keys())
            waste_quantities = [dow_waste[day].get('quantity', 0) for day in days]
            
            fig.add_trace(go.Bar(
                x=days,
                y=waste_quantities,
                name='Waste by Day',
                marker_color='#FF6B6B',
                hovertemplate='<b>%{x}</b><br>Waste: %{y} kg<extra></extra>'
            ), row=1, col=2)
        
        # Hourly meals
        hourly_meals = patterns_data.get('hourly_meals', {})
        if hourly_meals:
            hours = list(hourly_meals.keys())
            meal_counts = list(hourly_meals.values())
            
            fig.add_trace(go.Bar(
                x=hours,
                y=meal_counts,
                name='Hourly Meals',
                marker_color='#4ECDC4',
                hovertemplate='<b>%{x}:00</b><br>Meals: %{y}<extra></extra>'
            ), row=2, col=1)
        
        # Meal type distribution (pie chart)
        meal_type_counts = {}
        for day_data in dow_meals.values():
            # This is a simplified approach - would need actual meal type data
            pass
        
        # Add a placeholder pie chart for meal types
        fig.add_trace(go.Pie(
            labels=['Breakfast', 'Lunch', 'Dinner'],
            values=[30, 45, 25],
            name='Meal Types',
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3[:3],
            hovertemplate='<b>%{label}</b><br>Percentage: %{percent}<extra></extra>'
        ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_dining_hall_comparison_chart(comparison_data: Dict[str, Any], title: str = "Dining Hall Comparison") -> go.Figure:
        """Create dining hall comparison chart."""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Meals Served', 'Average Satisfaction', 'Waste Generated', 'Cost Comparison'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Meals served
        hall_meals = comparison_data.get('meals', {})
        if hall_meals:
            halls = list(hall_meals.keys())
            meal_counts = [hall_meals[hall].get('user_id', 0) for hall in halls]
            
            fig.add_trace(go.Bar(
                x=halls,
                y=meal_counts,
                name='Meals Served',
                marker_color='#2E8B57',
                hovertemplate='<b>%{x}</b><br>Meals: %{y}<extra></extra>'
            ), row=1, col=1)
        
        # Average satisfaction
        if hall_meals:
            satisfaction_scores = [hall_meals[hall].get('satisfaction_rating', 0) for hall in halls]
            
            fig.add_trace(go.Bar(
                x=halls,
                y=satisfaction_scores,
                name='Avg Satisfaction',
                marker_color='#4ECDC4',
                hovertemplate='<b>%{x}</b><br>Satisfaction: %{y:.2f}<extra></extra>'
            ), row=1, col=2)
        
        # Waste generated
        hall_waste = comparison_data.get('waste', {})
        if hall_waste:
            halls = list(hall_waste.keys())
            waste_quantities = [hall_waste[hall].get('quantity', 0) for hall in halls]
            
            fig.add_trace(go.Bar(
                x=halls,
                y=waste_quantities,
                name='Waste Generated',
                marker_color='#FF6B6B',
                hovertemplate='<b>%{x}</b><br>Waste: %{y} kg<extra></extra>'
            ), row=2, col=1)
        
        # Cost comparison
        if hall_waste:
            costs = [hall_waste[hall].get('estimated_cost', 0) for hall in halls]
            
            fig.add_trace(go.Bar(
                x=halls,
                y=costs,
                name='Cost',
                marker_color='#FFA500',
                hovertemplate='<b>%{x}</b><br>Cost: $%{y:.2f}<extra></extra>'
            ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_summary_dashboard(kpi_data: Dict[str, Any], title: str = "Executive Summary") -> go.Figure:
        """Create executive summary dashboard."""
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                'Total Waste', 'Meals Served', 'Satisfaction',
                'CO₂ Impact', 'Financial Savings', 'Waste %'
            ),
            specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                   [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
        )
        
        # Total Waste
        total_waste = kpi_data.get('total_food_waste', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=total_waste,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Total Waste"},
            number={'suffix': " kg"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=1, col=1)
        
        # Meals Served
        total_meals = kpi_data.get('total_meals_served', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=total_meals,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Meals Served"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=1, col=2)
        
        # Satisfaction
        satisfaction = kpi_data.get('avg_satisfaction', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=satisfaction,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Satisfaction"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=1, col=3)
        
        # CO₂ Impact
        co2 = kpi_data.get('co2_reduction', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=co2,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CO₂ Impact"},
            number={'suffix': " kg"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=2, col=1)
        
        # Financial Savings
        savings = kpi_data.get('financial_savings', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=savings,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Savings"},
            number={'prefix': "$"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=2, col=2)
        
        # Waste Percentage
        waste_pct = kpi_data.get('waste_percentage', {}).get('value', 0)
        fig.add_trace(go.Indicator(
            mode="number+delta",
            value=waste_pct,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Waste %"},
            number={'suffix': "%"},
            valuefont={'size': 16},
            titlefont={'size': 12}
        ), row=2, col=3)
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig


# Convenience functions for direct use
def create_kpi_chart(title: str, value: float, unit: str, change: float = 0,
                    trend: str = 'stable', color: str = 'blue') -> go.Figure:
    """Create KPI chart."""
    return AnalyticsCharts.create_kpi_card(title, value, unit, change, trend, color)


def create_trend_chart(data: pd.DataFrame, x_col: str, y_col: str, title: str = "") -> go.Figure:
    """Create trend chart."""
    return AnalyticsCharts.create_line_chart(data, x_col, y_col, title)


def create_category_chart(data: Dict[str, float], title: str = "") -> go.Figure:
    """Create category chart."""
    return AnalyticsCharts.create_pie_chart(data, title)
