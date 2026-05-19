"""
Forecast charts for AI forecasting system.
This module provides comprehensive visualization charts for
demand and waste forecasting using Plotly.
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


class ForecastCharts:
    """Chart creation for forecasting visualizations."""
    @staticmethod
    def create_demand_forecast_chart(historical_data: pd.DataFrame, 
                                   forecast_data: Dict[str, Any],
                                   title: str = "Demand Forecast") -> go.Figure:
        """Create demand forecast chart with historical data and predictions."""
        fig = go.Figure()
        
        # Add historical data
        if not historical_data.empty and 'date' in historical_data.columns and 'demand' in historical_data.columns:
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=historical_data['demand'],
                mode='lines+markers',
                name='Historical Demand',
                line=dict(color='#2E8B57', width=2),
                marker=dict(size=4, color='#2E8B57'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Demand:</b> %{y}<extra></extra>'
            ))
        
        # Add forecast data
        if 'predictions' in forecast_data:
            pred_dates = forecast_data.get('dates', [])
            pred_values = forecast_data['predictions']
            
            if isinstance(pred_values, np.ndarray):
                
                pred_values = pred_values.tolist()
            elif not isinstance(pred_values, list):
                pred_values = [pred_values]
            
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=pred_dates,
                y=pred_values,
                
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#FF6B6B', width=3, dash='dash'),
                marker=dict(size=6, color='#FF6B6B'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Predicted Demand:</b> %{y}<extra></extra>'
            ))
            
            # Confidence intervals
            if 'lower_bound' in forecast_data and 'upper_bound' in forecast_data:
                lower_bound = forecast_data['lower_bound']
                upper_bound = forecast_data['upper_bound']
                
                if isinstance(lower_bound, np.ndarray):
                    lower_bound = lower_bound.tolist()
                if isinstance(upper_bound, np.ndarray):
                    upper_bound = upper_bound.tolist()
                
                # Fill confidence interval
                fig.add_trace(go.Scatter(
                    x=pred_dates + pred_dates[::-1],
                    y=upper_bound + lower_bound[::-1],
                    fill='toself',
                    fillcolor='rgba(255, 107, 107, 0.2)',
                    line=dict(color='rgba(255, 107, 107, 0)'),
                    name='Confidence Interval',
                    hoverinfo="skip",
                    showlegend=True
                ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Demand (servings)",
            height=500,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    @staticmethod
    def create_waste_forecast_chart(historical_data: pd.DataFrame,
                                  forecast_data: Dict[str, Any],
                                  title: str = "Waste Forecast") -> go.Figure:
        """Create waste forecast chart with historical data and predictions."""
        fig = go.Figure()
        
        # Add historical data
        if not historical_data.empty and 'date' in historical_data.columns and 'quantity' in historical_data.columns:
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=historical_data['quantity'],
                mode='lines+markers',
                name='Historical Waste',
                line=dict(color='#DC3545', width=2),
                marker=dict(size=4, color='#DC3545'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Waste:</b> %{y} kg<extra></extra>'
            ))
        
        # Add forecast data
        if 'predictions' in forecast_data:
            pred_dates = forecast_data.get('dates', [])
            pred_values = forecast_data['predictions']
            
            if isinstance(pred_values, np.ndarray):
                pred_values = pred_values.tolist()
            elif not isinstance(pred_values, list):
                pred_values = [pred_values]
            
            # Main forecast line
            fig.add_trace(go.Scatter(
                x=pred_dates,
                y=pred_values,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#FFA500', width=3, dash='dash'),
                marker=dict(size=6, color='#FFA500'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Predicted Waste:</b> %{y} kg<extra></extra>'
            ))
            
            # Confidence intervals
            if 'lower_bound' in forecast_data and 'upper_bound' in forecast_data:
                lower_bound = forecast_data['lower_bound']
                upper_bound = forecast_data['upper_bound']
                
                if isinstance(lower_bound, np.ndarray):
                    lower_bound = lower_bound.tolist()
                if isinstance(upper_bound, np.ndarray):
                    upper_bound = upper_bound.tolist()
                
                # Fill confidence interval
                fig.add_trace(go.Scatter(
                    x=pred_dates + pred_dates[::-1],
                    y=upper_bound + lower_bound[::-1],
                    fill='toself',
                    fillcolor='rgba(255, 165, 0, 0.2)',
                    line=dict(color='rgba(255, 165, 0, 0)'),
                    name='Confidence Interval',
                    hoverinfo="skip",
                    showlegend=True
                ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Waste (kg)",
            height=500,
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    @staticmethod
    def create_category_waste_chart(category_predictions: Dict[str, float],
                                   title: str = "Waste by Category") -> go.Figure:
        """Create pie chart for waste by category."""
        if not category_predictions:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        # Sort categories by amount
        sorted_categories = sorted(category_predictions.items(), key=lambda x: x[1], reverse=True)
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[cat[0] for cat in sorted_categories],
            values=[cat[1] for cat in sorted_categories],
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3[:len(sorted_categories)],
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Waste: %{value:.2f} kg<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white',
            showlegend=True
        )
        
        return fig
    
    @staticmethod
    def create_model_performance_chart(metrics: Dict[str, Any],
                                    title: str = "Model Performance") -> go.Figure:
        """Create model performance comparison chart."""
        models = list(metrics.keys())
        mae_values = [metrics[model]['mae'] for model in models]
        rmse_values = [metrics[model]['rmse'] for model in models]
        r2_values = [metrics[model]['r2'] for model in models]
        
        fig = make_subplots(
            rows=1, cols=3,
            subplot_titles=('MAE (Lower is Better)', 'RMSE (Lower is Better)', 'R² (Higher is Better)'),
            specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
        )
        
        # MAE chart
        fig.add_trace(go.Bar(
            x=models,
            y=mae_values,
            name='MAE',
            marker_color='#2E8B57',
            hovertemplate='<b>Model:</b> %{x}<br>MAE: %{y:.2f}<extra></extra>'
        ), row=1, col=1)
        
        # RMSE chart
        fig.add_trace(go.Bar(
            x=models,
            y=rmse_values,
            name='RMSE',
            marker_color='#FF6B6B',
            hovertemplate='<b>Model:</b> %{x}<br>RMSE: %{y:.2f}<extra></extra>'
        ), row=1, col=2)
        
        # R² chart
        fig.add_trace(go.Bar(
            x=models,
            y=r2_values,
            name='R²',
            marker_color='#4ECDC4',
            hovertemplate='<b>Model:</b> %{x}<br>R²: %{y:.3f}<extra></extra>'
        ), row=1, col=3)
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_feature_importance_chart(importance_dict: Dict[str, float],
                                     title: str = "Feature Importance") -> go.Figure:
        """Create feature importance chart."""
        if not importance_dict:
            fig = go.Figure()
            fig.add_annotation(
                text="No feature importance data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        # Sort features by importance
        sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # Create horizontal bar chart
        fig = go.Figure(data=[go.Bar(
            x=[feature[1] for feature in sorted_features],
            y=[feature[0] for feature in sorted_features],
            orientation='h',
            marker_color='#FF6B6B',
            hovertemplate='<b>Feature:</b> %{y}<br>Importance: %{x:.3f}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Importance",
            yaxis_title="Features",
            height=max(400, len(sorted_features) * 30),
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_forecast_comparison_chart(actual_data: pd.DataFrame,
                                      forecast_data: Dict[str, Any],
                                      title: str = "Forecast vs Actual") -> go.Figure:
        """Create comparison chart between forecast and actual values."""
        fig = go.Figure()
        
        # Add actual data
        if not actual_data.empty and 'date' in actual_data.columns:
            value_column = 'demand' if 'demand' in actual_data.columns else 'quantity'
            
            fig.add_trace(go.Scatter(
                x=actual_data['date'],
                y=actual_data[value_column],
                mode='lines+markers',
                name='Actual',
                line=dict(color='#2E8B57', width=2),
                marker=dict(size=4, color='#2E8B57'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Actual:</b> %{y}<extra></extra>'
            ))
        
        # Add forecast data
        if 'predictions' in forecast_data:
            pred_dates = forecast_data.get('dates', [])
            pred_values = forecast_data['predictions']
            
            if isinstance(pred_values, np.ndarray):
                pred_values = pred_values.tolist()
            elif not isinstance(pred_values, list):
                pred_values = [pred_values]
            
            fig.add_trace(go.Scatter(
                x=pred_dates,
                y=pred_values,
                mode='lines+markers',
                name='Forecast',
                line=dict(color='#FF6B6B', width=2, dash='dash'),
                marker=dict(size=4, color='#FF6B6B'),
                hovertemplate='<b>Date:</b> %{x}<br><b>Forecast:</b> %{y}<extra></extra>'
            ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Value",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_residuals_chart(actual_values: List[float],
                            predicted_values: List[float],
                            title: str = "Residuals Analysis") -> go.Figure:
        """Create residuals analysis chart."""
        # Calculate residuals
        residuals = np.array(actual_values) - np.array(predicted_values)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Residuals vs Predicted', 'Residuals Distribution', 
                          'Q-Q Plot', 'Residuals Time Series'),
            specs=[[{"type": "scatter"}, {"type": "histogram"}],
                   [{"type": "scatter"}, {"type": "scatter"}]]
        )
        
        # Residuals vs Predicted
        fig.add_trace(go.Scatter(
            x=predicted_values,
            y=residuals,
            mode='markers',
            name='Residuals',
            marker=dict(color='#FF6B6B', size=4),
            hovertemplate='<b>Predicted:</b> %{x}<br><b>Residual:</b> %{y}<extra></extra>'
        ), row=1, col=1)
        
        # Add zero line
        fig.add_trace(go.Scatter(
            x=[min(predicted_values), max(predicted_values)],
            y=[0, 0],
            mode='lines',
            name='Zero Line',
            line=dict(color='black', dash='dash'),
            showlegend=False
        ), row=1, col=1)
        
        # Residuals distribution
        fig.add_trace(go.Histogram(
            x=residuals,
            nbinsx=20,
            name='Residuals Distribution',
            marker_color='#4ECDC4',
            hovertemplate='<b>Residual:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>'
        ), row=1, col=2)
        
        # Q-Q Plot (simplified)
        sorted_residuals = np.sort(residuals)
        theoretical_quantiles = np.linspace(-3, 3, len(sorted_residuals))
        
        fig.add_trace(go.Scatter(
            x=theoretical_quantiles,
            y=sorted_residuals,
            mode='markers',
            name='Q-Q Plot',
            marker=dict(color='#2E8B57', size=4),
            hovertemplate='<b>Theoretical:</b> %{x}<br><b>Actual:</b> %{y}<extra></extra>'
        ), row=2, col=1)
        
        # Add diagonal line for Q-Q plot
        min_val = min(theoretical_quantiles.min(), sorted_residuals.min())
        max_val = max(theoretical_quantiles.max(), sorted_residuals.max())
        
        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Diagonal',
            line=dict(color='black', dash='dash'),
            showlegend=False
        ), row=2, col=1)
        
        # Residuals time series
        fig.add_trace(go.Scatter(
            x=list(range(len(residuals))),
            y=residuals,
            mode='lines+markers',
            name='Residuals Over Time',
            line=dict(color='#FFA500', width=1),
            marker=dict(size=3, color='#FFA500'),
            hovertemplate='<b>Index:</b> %{x}<br><b>Residual:</b> %{y}<extra></extra>'
        ), row=2, col=2)
        
        # Add zero line for time series
        fig.add_trace(go.Scatter(
            x=[0, len(residuals)-1],
            y=[0, 0],
            mode='lines',
            name='Zero Line',
            line=dict(color='black', dash='dash'),
            showlegend=False
        ), row=2, col=2)
        
        fig.update_layout(
            title=title,
            height=600,
            template='plotly_white',
            showlegend=False
        )
        
        return fig
    
    @staticmethod
    def create_weekly_forecast_chart(weekly_data: Dict[str, Any],
                                   title: str = "Weekly Forecast") -> go.Figure:
        """Create weekly forecast chart."""
        fig = go.Figure()
        
        daily_predictions = weekly_data.get('daily_predictions', [])
        
        if daily_predictions:
            # Group by meal type
            breakfast_data = []
            lunch_data = []
            dinner_data = []
            dates = []
            
            for pred in daily_predictions:
                dates.append(pred.get('date', ''))
                meal_type = pred.get('meal_type', '')
                demand = pred.get('predicted_demand', 0)
                
                if meal_type == 'breakfast':
                    breakfast_data.append(demand)
                elif meal_type == 'lunch':
                    lunch_data.append(demand)
                elif meal_type == 'dinner':
                    dinner_data.append(demand)
            
            # Add traces for each meal type
            if breakfast_data:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=breakfast_data,
                    mode='lines+markers',
                    name='Breakfast',
                    line=dict(color='#FFA500', width=2),
                    marker=dict(size=6, color='#FFA500'),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Breakfast Demand:</b> %{y}<extra></extra>'
                ))
            
            if lunch_data:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=lunch_data,
                    mode='lines+markers',
                    name='Lunch',
                    line=dict(color='#2E8B57', width=2),
                    marker=dict(size=6, color='#2E8B57'),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Lunch Demand:</b> %{y}<extra></extra>'
                ))
            
            if dinner_data:
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=dinner_data,
                    mode='lines+markers',
                    name='Dinner',
                    line=dict(color='#DC3545', width=2),
                    marker=dict(size=6, color='#DC3545'),
                    hovertemplate='<b>Date:</b> %{x}<br><b>Dinner Demand:</b> %{y}<extra></extra>'
                ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Predicted Demand",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        return fig
    
    @staticmethod
    def create_recommendation_chart(recommendations: List[str],
                                  metrics: Dict[str, Any],
                                  title: str = "AI Recommendations") -> go.Figure:
        """Create recommendation visualization."""
        fig = go.Figure()
        
        # Create a simple table-like visualization
        fig.add_annotation(
            text="<b>AI-Powered Recommendations</b>",
            xref="paper", yref="paper",
            x=0.5, y=0.95, showarrow=False,
            font=dict(size=16, color="#2E8B57")
        )
        
        # Add recommendations
        for i, rec in enumerate(recommendations[:5], 1):
            fig.add_annotation(
                text=f"{i}. {rec}",
                xref="paper", yref="paper",
                x=0.05, y=0.85 - (i-1)*0.15, showarrow=False,
                font=dict(size=12, color="black"),
                align="left"
            )
        
        # Add key metrics
        y_pos = 0.85 - len(recommendations[:5])*0.15 - 0.1
        
        if metrics:
            fig.add_annotation(
                text="<b>Key Metrics</b>",
                xref="paper", yref="paper",
                x=0.5, y=y_pos, showarrow=False,
                font=dict(size=14, color="#FF6B6B")
            )
            
            metric_items = list(metrics.items())[:3]
            for i, (key, value) in enumerate(metric_items, 1):
                fig.add_annotation(
                    text=f"• {key}: {value}",
                    xref="paper", yref="paper",
                    x=0.05, y=y_pos - 0.08*i, showarrow=False,
                    font=dict(size=11, color="black"),
                    align="left"
                )
        
        fig.update_layout(
            title=title,
            height=400,
            template='plotly_white',
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
    
    @staticmethod
    def create_model_accuracy_chart(accuracy_metrics: Dict[str, float],
                                 title: str = "Model Accuracy") -> go.Figure:
        """Create model accuracy gauge chart."""
        # Calculate overall accuracy
        if 'mape' in accuracy_metrics:
            mape = accuracy_metrics['mape']
            accuracy = max(0, min(100, 100 - mape))
        elif 'r2' in accuracy_metrics:
            accuracy = accuracy_metrics['r2'] * 100
        else:
            accuracy = 85  # Default
        
        # Determine color based on accuracy
        if accuracy >= 90:
            color = '#28A745'  # Green
        elif accuracy >= 80:
            color = '#FFC107'  # Yellow
        elif accuracy >= 70:
            color = '#FD7E14'  # Orange
        else:
            color = '#DC3545'  # Red
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=accuracy,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Model Accuracy"},
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
            title=title,
            height=300,
            template='plotly_white'
        )
        
        return fig
    
    @staticmethod
    def create_seasonal_pattern_chart(data: pd.DataFrame,
                                    title: str = "Seasonal Patterns") -> go.Figure:
        """Create seasonal pattern analysis chart."""
        if data.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available for seasonal analysis",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray")
            )
            fig.update_layout(title=title, height=400)
            return fig
        
        # Add season column if not present
        if 'date' in data.columns:
            data['season'] = data['date'].dt.month.apply(lambda x: 
                'Winter' if x in [12, 1, 2] else
                'Spring' if x in [3, 4, 5] else
                'Summer' if x in [6, 7, 8] else 'Fall'
            )
        
        # Group by season
        value_column = 'demand' if 'demand' in data.columns else 'quantity'
        seasonal_data = data.groupby('season')[value_column].agg(['mean', 'std']).reset_index()
        
        # Create bar chart with error bars
        fig = go.Figure(data=[go.Bar(
            x=seasonal_data['season'],
            y=seasonal_data['mean'],
            error_y=dict(type='data', array=seasonal_data['std']),
            name='Average',
            marker_color=['#87CEEB', '#90EE90', '#FFD700', '#FFA07A'],
            hovertemplate='<b>Season:</b> %{x}<br>Average: %{y:.2f}<br>Std Dev: %{error_y.array:.2f}<extra></extra>'
        )])
        
        fig.update_layout(
            title=title,
            xaxis_title="Season",
            yaxis_title="Average Value",
            height=400,
            template='plotly_white',
            showlegend=False
        )
        
        return fig


# Convenience functions for direct use
def create_demand_chart(historical_data: pd.DataFrame, forecast_data: Dict[str, Any]) -> go.Figure:
    """Create demand forecast chart."""
    return ForecastCharts.create_demand_forecast_chart(historical_data, forecast_data)


def create_waste_chart(historical_data: pd.DataFrame, forecast_data: Dict[str, Any]) -> go.Figure:
    """Create waste forecast chart."""
    return ForecastCharts.create_waste_forecast_chart(historical_data, forecast_data)


def create_performance_chart(metrics: Dict[str, Any]) -> go.Figure:
    """Create model performance chart."""
    return ForecastCharts.create_model_performance_chart(metrics)
