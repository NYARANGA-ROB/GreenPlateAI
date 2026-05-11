"""
Professional analytics dashboard for GreenPlateAI.

This module provides a comprehensive analytics dashboard with
KPI cards, interactive charts, and exportable summaries.
"""

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Initialize database first
from database.init_db import init_database
init_database(create_sample_data=True)

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import json

# Import analytics components
from data_aggregator import AnalyticsDataAggregator, get_dashboard_data, export_dashboard_summary
from charts import AnalyticsCharts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Analytics Dashboard - GreenPlateAI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for responsive design
st.markdown("""
<style>
.analytics-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
    transition: transform 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.chart-container {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}

.metric-value {
    font-size: 2rem;
    font-weight: bold;
    color: #2c3e50;
}

.metric-label {
    font-size: 0.9rem;
    color: #7f8c8d;
    margin-bottom: 0.5rem;
}

.metric-change {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    display: inline-block;
}

.change-positive {
    background-color: #d4edda;
    color: #155724;
}

.change-negative {
    background-color: #f8d7da;
    color: #721c24;
}

.change-neutral {
    background-color: #f8f9fa;
    color: #6c757d;
}

.trend-up {
    color: #28a745;
}

.trend-down {
    color: #dc3545;
}

.trend-stable {
    color: #6c757d;
}

.filter-section {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border: 1px solid #dee2e6;
}

.export-section {
    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    color: white;
    border-radius: 10px;
    padding: 1.5rem;
    margin-top: 2rem;
    text-align: center;
}

.summary-card {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border-left: 4px solid #28a745;
}

@media (max-width: 768px) {
    .kpi-grid {
        grid-template-columns: 1fr;
    }
    
    .chart-container {
        padding: 1rem;
    }
    
    .analytics-header {
        padding: 1rem;
    }
    
    .analytics-header h1 {
        font-size: 1.5rem;
    }
}

/* Responsive chart sizing */
@media (max-width: 768px) {
    .js-plotly-plot .plotly {
        width: 100% !important;
    }
}

/* Custom scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #555;
}
</style>
""", unsafe_allow_html=True)


class AnalyticsDashboard:
    """Main analytics dashboard class."""
    
    def __init__(self):
        """Initialize the dashboard."""
        self.aggregator = AnalyticsDataAggregator()
        self.charts = AnalyticsCharts()
        
        # Initialize session state
        if 'dashboard_data' not in st.session_state:
            st.session_state.dashboard_data = None
        if 'selected_period' not in st.session_state:
            st.session_state.selected_period = 'Last 30 Days'
        if 'selected_dining_hall' not in st.session_state:
            st.session_state.selected_dining_hall = 'All'
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
    
    def run(self):
        """Run the main dashboard."""
        # Check authentication
        if not self._check_authentication():
            return
        
        # Header
        self._show_header()
        
        # Sidebar filters
        self._show_sidebar()
        
        # Load data
        dashboard_data = self._load_data()
        
        if dashboard_data:
            # Main content
            self._show_kpi_cards(dashboard_data)
            self._show_main_charts(dashboard_data)
            self._show_detailed_analysis(dashboard_data)
            self._show_export_section(dashboard_data)
        else:
            self._show_no_data_message()
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        if 'user' not in st.session_state:
            st.error("🔐 Please log in to access the analytics dashboard.")
            st.info("Please log in from the main application.")
            return False
        return True
    
    def _show_header(self):
        """Show dashboard header."""
        st.markdown("""
        <div class="analytics-header">
            <h1>📊 GreenPlateAI Analytics Dashboard</h1>
            <p>Real-time insights into food waste, meal popularity, and sustainability metrics</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_sidebar(self):
        """Show sidebar with filters and controls."""
        with st.sidebar:
            st.markdown("### 🔍 Filters & Controls")
            
            # Date range selection
            st.markdown("#### 📅 Date Range")
            
            date_options = {
                "Today": (date.today(), date.today()),
                "Yesterday": (date.today() - timedelta(days=1), date.today() - timedelta(days=1)),
                "Last 7 Days": (date.today() - timedelta(days=6), date.today()),
                "Last 30 Days": (date.today() - timedelta(days=29), date.today()),
                "Last 90 Days": (date.today() - timedelta(days=89), date.today()),
                "This Month": (date.today().replace(day=1), date.today()),
                "Last Month": (
                    (date.today().replace(day=1) - timedelta(days=1)).replace(day=1),
                    date.today().replace(day=1) - timedelta(days=1)
                ),
                "Custom Range": None
            }
            
            selected_period = st.selectbox(
                "Select Period",
                options=list(date_options.keys()),
                index=3,  # Default to "Last 30 Days"
            )
            
            if selected_period == "Custom Range":
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", date.today() - timedelta(days=29))
                with col2:
                    end_date = st.date_input("End Date", date.today())
                
                if start_date > end_date:
                    st.error("Start date cannot be after end date")
                    return
            else:
                start_date, end_date = date_options[selected_period]
            
            st.session_state.selected_period = selected_period
            st.session_state.start_date = start_date
            st.session_state.end_date = end_date
            
            # Dining hall filter
            st.markdown("#### 🏢 Dining Hall")
            
            dining_halls = ["All", "Main Hall", "North Campus", "South Campus", "West Campus"]
            selected_hall = st.selectbox(
                "Select Dining Hall",
                options=dining_halls,
                index=0
            )
            
            st.session_state.selected_dining_hall = selected_hall
            
            # Auto-refresh
            st.markdown("#### 🔄 Auto Refresh")
            
            auto_refresh = st.checkbox(
                "Enable Auto Refresh",
                value=st.session_state.auto_refresh,
                help="Automatically refresh data every 5 minutes"
            )
            
            st.session_state.auto_refresh = auto_refresh
            
            if auto_refresh:
                st.info("🔄 Dashboard will auto-refresh every 5 minutes")
            
            # Quick actions
            st.markdown("#### ⚡ Quick Actions")
            
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.session_state.dashboard_data = None
                st.experimental_rerun()
            
            if st.button("📥 Export Report", use_container_width=True):
                self._export_data()
            
            # Data info
            if st.session_state.dashboard_data:
                data = st.session_state.dashboard_data
                period = data.get('period', {})
                
                st.markdown("#### 📊 Data Summary")
                st.info(f"""
                **Period**: {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')}  
                **Days**: {period.get('days', 0)}  
                **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)
    
    def _load_data(self) -> Dict[str, Any]:
        """Load dashboard data."""
        if st.session_state.dashboard_data is None:
            with st.spinner("Loading analytics data..."):
                try:
                    start_date = st.session_state.start_date
                    end_date = st.session_state.end_date
                    dining_hall = st.session_state.selected_dining_hall
                    
                    if dining_hall == "All":
                        dining_hall = None
                    
                    dashboard_data = self.aggregator.get_dashboard_data(start_date, end_date, dining_hall)
                    st.session_state.dashboard_data = dashboard_data
                    
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
                    logger.error(f"Error loading dashboard data: {str(e)}")
                    return None
        
        return st.session_state.dashboard_data
    
    def _show_kpi_cards(self, data: Dict[str, Any]):
        """Show KPI cards."""
        st.markdown("### 📊 Key Performance Indicators")
        
        kpi_metrics = data.get('kpi_metrics', {})
        
        # Create KPI grid
        col1, col2, col3, col4 = st.columns(4)
        
        kpi_configs = [
            {
                'title': 'Total Food Waste',
                'value': kpi_metrics.get('total_food_waste', {}).get('value', 0),
                'unit': kpi_metrics.get('total_food_waste', {}).get('unit', 'kg'),
                'change': kpi_metrics.get('total_food_waste', {}).get('change', 0),
                'trend': kpi_metrics.get('total_food_waste', {}).get('trend', 'stable'),
                'color': 'red'
            },
            {
                'title': 'Meals Served',
                'value': kpi_metrics.get('total_meals_served', {}).get('value', 0),
                'unit': kpi_metrics.get('total_meals_served', {}).get('unit', 'meals'),
                'change': kpi_metrics.get('total_meals_served', {}).get('change', 0),
                'trend': kpi_metrics.get('total_meals_served', {}).get('trend', 'stable'),
                'color': 'green'
            },
            {
                'title': 'Student Satisfaction',
                'value': kpi_metrics.get('avg_satisfaction', {}).get('value', 0),
                'unit': kpi_metrics.get('avg_satisfaction', {}).get('unit', 'score'),
                'change': kpi_metrics.get('avg_satisfaction', {}).get('change', 0),
                'trend': kpi_metrics.get('avg_satisfaction', {}).get('trend', 'stable'),
                'color': 'blue'
            },
            {
                'title': 'CO₂ Reduction',
                'value': kpi_metrics.get('co2_reduction', {}).get('value', 0),
                'unit': kpi_metrics.get('co2_reduction', {}).get('unit', 'kg'),
                'change': kpi_metrics.get('co2_reduction', {}).get('change', 0),
                'trend': kpi_metrics.get('co2_reduction', {}).get('trend', 'stable'),
                'color': 'purple'
            }
        ]
        
        cols = [col1, col2, col3, col4]
        
        for i, config in enumerate(kpi_configs):
            with cols[i]:
                self._create_kpi_card(config)
        
        # Second row of KPIs
        col5, col6, col7 = st.columns(3)
        
        additional_kpis = [
            {
                'title': 'Financial Savings',
                'value': kpi_metrics.get('financial_savings', {}).get('value', 0),
                'unit': kpi_metrics.get('financial_savings', {}).get('unit', '$'),
                'change': kpi_metrics.get('financial_savings', {}).get('change', 0),
                'trend': kpi_metrics.get('financial_savings', {}).get('trend', 'stable'),
                'color': 'orange'
            },
            {
                'title': 'Waste Percentage',
                'value': kpi_metrics.get('waste_percentage', {}).get('value', 0),
                'unit': kpi_metrics.get('waste_percentage', {}).get('unit', '%'),
                'change': kpi_metrics.get('waste_percentage', {}).get('change', 0),
                'trend': kpi_metrics.get('waste_percentage', {}).get('trend', 'stable'),
                'color': 'teal'
            },
            {
                'title': 'Cost per Meal',
                'value': data.get('financial_metrics', {}).get('cost_per_meal', 0),
                'unit': '$',
                'change': 0,  # Would need historical data
                'trend': 'stable',
                'color': 'indigo'
            }
        ]
        
        additional_cols = [col5, col6, col7]
        
        for i, config in enumerate(additional_kpis):
            with additional_cols[i]:
                self._create_kpi_card(config)
    
    def _create_kpi_card(self, config: Dict[str, Any]):
        """Create individual KPI card."""
        # Determine trend icon and color
        trend_icons = {
            'increasing': '📈',
            'decreasing': '📉',
            'stable': '➡️'
        }
        
        trend_colors = {
            'increasing': 'trend-up',
            'decreasing': 'trend-down',
            'stable': 'trend-stable'
        }
        
        change_value = config.get('change', 0)
        trend = config.get('trend', 'stable')
        
        # Determine change class
        if change_value > 5:
            change_class = 'change-positive'
        elif change_value < -5:
            change_class = 'change-negative'
        else:
            change_class = 'change-neutral'
        
        # Format value
        value = config.get('value', 0)
        unit = config.get('unit', '')
        
        if unit == '$':
            formatted_value = f"${value:,.2f}"
        elif unit == 'kg':
            formatted_value = f"{value:,.1f}"
        elif unit == '%':
            formatted_value = f"{value:.1f}%"
        elif unit == 'score':
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = f"{value:,.0f}"
        
        st.markdown(f"""
        <div class="kpi-card">
            <div class="metric-label">{config.get('title', 'Metric')}</div>
            <div class="metric-value">{formatted_value}</div>
            <div class="metric-change {change_class}">
                {trend_icons.get(trend, '➡️')} {change_value:+.1f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_main_charts(self, data: Dict[str, Any]):
        """Show main charts section."""
        st.markdown("### 📈 Trend Analysis")
        
        # Weekly and Monthly Trends
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Weekly Trends")
            weekly_data = data.get('trends', {}).get('weekly', {})
            if weekly_data:
                fig = self.charts.create_weekly_trends_chart(weekly_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No weekly data available")
        
        with col2:
            st.markdown("#### 📊 Monthly Trends")
            monthly_data = data.get('trends', {}).get('monthly', {})
            if monthly_data:
                fig = self.charts.create_monthly_trends_chart(monthly_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly data available")
        
        # Meal Popularity and Satisfaction
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🍽️ Meal Popularity")
            popularity_data = data.get('meal_popularity', {})
            if popularity_data:
                fig = self.charts.create_meal_popularity_chart(popularity_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No popularity data available")
        
        with col2:
            st.markdown("#### 😊 Student Satisfaction")
            satisfaction_data = data.get('student_satisfaction', {})
            if satisfaction_data:
                fig = self.charts.create_satisfaction_chart(satisfaction_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No satisfaction data available")
    
    def _show_detailed_analysis(self, data: Dict[str, Any]):
        """Show detailed analysis section."""
        st.markdown("### 🔍 Detailed Analysis")
        
        # Environmental Impact and Financial Metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🌍 Environmental Impact")
            impact_data = data.get('environmental_impact', {})
            if impact_data:
                fig = self.charts.create_environmental_impact_chart(impact_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No environmental impact data available")
        
        with col2:
            st.markdown("#### 💰 Financial Metrics")
            financial_data = data.get('financial_metrics', {})
            if financial_data:
                fig = self.charts.create_financial_chart(financial_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No financial data available")
        
        # Category Analysis and Time Patterns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📦 Category Analysis")
            category_data = data.get('category_analysis', {})
            if category_data:
                fig = self.charts.create_category_analysis_chart(category_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        with col2:
            st.markdown("#### ⏰ Time Patterns")
            patterns_data = data.get('time_patterns', {})
            if patterns_data:
                fig = self.charts.create_time_patterns_chart(patterns_data)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No pattern data available")
        
        # Dining Hall Comparison
        st.markdown("#### 🏢 Dining Hall Comparison")
        comparison_data = data.get('dining_hall_comparison', {})
        if comparison_data:
            fig = self.charts.create_dining_hall_comparison_chart(comparison_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No comparison data available")
    
    def _show_export_section(self, data: Dict[str, Any]):
        """Show export section."""
        st.markdown("""
        <div class="export-section">
            <h3>📥 Export Summary Report</h3>
            <p>Download comprehensive analytics reports in various formats</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export as JSON", use_container_width=True):
                self._export_data('json')
        
        with col2:
            if st.button("📊 Export as CSV", use_container_width=True):
                self._export_data('csv')
        
        with col3:
            if st.button("📋 Generate Summary", use_container_width=True):
                self._generate_summary(data)
    
    def _export_data(self, format: str = 'json'):
        """Export dashboard data."""
        try:
            if st.session_state.dashboard_data:
                filename = self.aggregator.export_summary(st.session_state.dashboard_data, format)
                st.success(f"✅ Data exported successfully to {filename}")
            else:
                st.warning("⚠️ No data available to export")
        except Exception as e:
            st.error(f"❌ Error exporting data: {str(e)}")
    
    def _generate_summary(self, data: Dict[str, Any]):
        """Generate executive summary."""
        st.markdown("### 📋 Executive Summary")
        
        # Create summary sections
        kpi_metrics = data.get('kpi_metrics', {})
        
        # Performance Overview
        st.markdown("#### 🎯 Performance Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_waste = kpi_metrics.get('total_food_waste', {}).get('value', 0)
            st.metric("Total Waste", f"{total_waste:.1f} kg")
        
        with col2:
            total_meals = kpi_metrics.get('total_meals_served', {}).get('value', 0)
            st.metric("Meals Served", f"{total_meals:,}")
        
        with col3:
            satisfaction = kpi_metrics.get('avg_satisfaction', {}).get('value', 0)
            st.metric("Avg Satisfaction", f"{satisfaction:.2f}")
        
        # Key Insights
        st.markdown("#### 💡 Key Insights")
        
        insights = []
        
        # Waste insights
        if total_waste > 100:
            insights.append("🔴 High waste levels detected - immediate attention needed")
        elif total_waste > 50:
            insights.append("🟡 Moderate waste levels - consider optimization")
        else:
            insights.append("🟢 Waste levels within acceptable range")
        
        # Satisfaction insights
        if satisfaction > 4.0:
            insights.append("✅ Excellent student satisfaction ratings")
        elif satisfaction > 3.5:
            insights.append("👍 Good student satisfaction ratings")
        else:
            insights.append("⚠️ Student satisfaction needs improvement")
        
        # Financial insights
        financial_savings = kpi_metrics.get('financial_savings', {}).get('value', 0)
        if financial_savings > 1000:
            insights.append("💰 Significant cost savings achieved")
        elif financial_savings > 500:
            insights.append("💵 Moderate cost savings achieved")
        else:
            insights.append("📈 Opportunity for cost optimization")
        
        for insight in insights:
            st.info(insight)
        
        # Recommendations
        st.markdown("#### 🎯 Recommendations")
        
        recommendations = []
        
        if total_waste > 50:
            recommendations.append("Implement waste reduction strategies")
        
        if satisfaction < 4.0:
            recommendations.append("Focus on improving meal quality and variety")
        
        if financial_savings < 500:
            recommendations.append("Optimize purchasing and inventory management")
        
        recommendations.extend([
            "Continue monitoring environmental impact",
            "Engage students in sustainability initiatives",
            "Regularly review and adjust menu offerings"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"{i}. {rec}")
    
    def _show_no_data_message(self):
        """Show message when no data is available."""
        st.markdown("""
        <div class="chart-container" style="text-align: center; padding: 3rem;">
            <h3>📊 No Data Available</h3>
            <p>There is no data available for the selected period and filters.</p>
            <p>Please try adjusting your filters or check back later.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Suggestions
        st.markdown("### 💡 Suggestions")
        
        suggestions = [
            "Try selecting a different date range",
            "Check if data is being logged in the system",
            "Verify that the dining hall has active operations",
            "Contact support if the issue persists"
        ]
        
        for suggestion in suggestions:
            st.info(f"• {suggestion}")


def main():
    """Main function to run the analytics dashboard."""
    try:
        dashboard = AnalyticsDashboard()
        dashboard.run()
        
        # Auto-refresh functionality
        if st.session_state.get('auto_refresh', False):
            # Refresh every 5 minutes (300 seconds)
            time.sleep(300)
            st.experimental_rerun()
            
    except Exception as e:
        logger.error(f"Error running analytics dashboard: {str(e)}")
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please refresh the page and try again.")


if __name__ == "__main__":
    main()
