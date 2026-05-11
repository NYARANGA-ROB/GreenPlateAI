"""
Main Streamlit application for Food Waste Logging module.

This module provides the complete waste logging interface with
forms, data visualization, and management features.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging

# Import waste logging components
from database.connection import get_session
from database.models import FoodWasteLog, WasteCategory, MealType
from waste_logging.forms import WasteLoggingForms
from waste_logging.database_ops import WasteLoggingDB
from waste_logging.charts import WasteLoggingCharts
from waste_logging.helpers import WasteLoggingHelpers
from waste_logging.validators import ValidationUtils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Food Waste Logging - GreenPlateAI",
    page_icon="🗑️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.waste-header {
    background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%);
    color: white;
    padding: 2rem;
    border-radius: 10px;
    margin-bottom: 2rem;
    text-align: center;
}

.metric-card {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border-left: 4px solid #FF6B6B;
    margin-bottom: 1rem;
}

.form-section {
    background: white;
    border-radius: 10px;
    padding: 2rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.chart-container {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}

.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
    border: 1px solid #c3e6cb;
}

.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
    border: 1px solid #f5c6cb;
}

.warning-message {
    background-color: #fff3cd;
    color: #856404;
    padding: 1rem;
    border-radius: 5px;
    margin-bottom: 1rem;
    border: 1px solid #ffeaa7;
}
</style>
""", unsafe_allow_html=True)


class WasteLoggingApp:
    """Main application class for waste logging."""
    
    def __init__(self):
        """Initialize the application."""
        self.session = get_session()
        self.db_ops = WasteLoggingDB(self.session)
        self.forms = WasteLoggingForms()
        self.charts = WasteLoggingCharts()
        
        # Initialize session state
        if 'page' not in st.session_state:
            st.session_state.page = 'dashboard'
        
        if 'selected_dining_hall' not in st.session_state:
            st.session_state.selected_dining_hall = None
        
        if 'date_range' not in st.session_state:
            st.session_state.date_range = ('Last 7 Days', date.today() - timedelta(days=6), date.today())
    
    def run(self):
        """Run the main application."""
        # Check authentication
        if not self._check_authentication():
            return
        
        # Header
        self._show_header()
        
        # Sidebar navigation
        self._show_sidebar()
        
        # Main content based on page
        if st.session_state.page == 'dashboard':
            self._show_dashboard()
        elif st.session_state.page == 'meal_preparation':
            self._show_meal_preparation()
        elif st.session_state.page == 'leftovers':
            self._show_leftovers()
        elif st.session_state.page == 'disposed_food':
            self._show_disposed_food()
        elif st.session_state.page == 'serving_quantities':
            self._show_serving_quantities()
        elif st.session_state.page == 'daily_report':
            self._show_daily_report()
        elif st.session_state.page == 'data_view':
            self._show_data_view()
        elif st.session_state.page == 'analytics':
            self._show_analytics()
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        if 'user' not in st.session_state:
            st.error("🔐 Please log in to access the waste logging module.")
            st.info("Please log in from the main application.")
            return False
        return True
    
    def _show_header(self):
        """Show application header."""
        st.markdown("""
        <div class="waste-header">
            <h1>🗑️ Food Waste Logging</h1>
            <p>Track, analyze, and reduce food waste in university dining services</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_sidebar(self):
        """Show sidebar navigation and filters."""
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            # Navigation menu
            pages = {
                'dashboard': '📊 Dashboard',
                'meal_preparation': '🍳 Meal Preparation',
                'leftovers': '🥡 Leftovers',
                'disposed_food': '🗑️ Disposed Food',
                'serving_quantities': '🍽️ Serving Quantities',
                'daily_report': '📤 Daily Report',
                'data_view': '📋 Data View',
                'analytics': '📈 Analytics'
            }
            
            for page_key, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.page = page_key
                    st.experimental_rerun()
            
            st.markdown("---")
            st.markdown("### 🔍 Filters")
            
            # Dining hall filter
            dining_halls = self.db_ops.get_dining_halls_list()
            if dining_halls:
                selected_hall = st.selectbox(
                    "Dining Hall",
                    options=["All"] + dining_halls,
                    key="filter_dining_hall"
                )
                st.session_state.selected_dining_hall = selected_hall if selected_hall != "All" else None
            else:
                st.session_state.selected_dining_hall = None
            
            # Date range filter
            date_presets = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "This Week", "This Month"]
            selected_preset = st.selectbox(
                "Date Range",
                options=date_presets,
                key="filter_date_preset"
            )
            
            # Get date range
            start_date, end_date = WasteLoggingHelpers.get_date_range_preset(selected_preset)
            st.session_state.date_range = (selected_preset, start_date, end_date)
            
            # Show date range info
            st.info(f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            st.markdown("---")
            st.markdown("### 📊 Quick Stats")
            
            # Get filtered data
            waste_logs = self._get_filtered_waste_logs()
            
            if waste_logs:
                summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
                
                st.metric("Total Waste", f"{summary['total_waste_kg']:.1f} kg")
                st.metric("Total Cost", f"${summary['total_cost']:.2f}")
                st.metric("Entries", summary['total_entries'])
            else:
                st.info("No data available for selected filters")
    
    def _get_filtered_waste_logs(self) -> List[FoodWasteLog]:
        """Get waste logs based on current filters."""
        _, start_date, end_date = st.session_state.date_range
        dining_hall = st.session_state.selected_dining_hall
        
        return self.db_ops.get_waste_logs_by_date_range(
            start_date=start_date,
            end_date=end_date,
            dining_hall=dining_hall
        )
    
    def _show_dashboard(self):
        """Show main dashboard."""
        st.markdown("## 📊 Waste Dashboard")
        
        # Get filtered data
        waste_logs = self._get_filtered_waste_logs()
        
        if not waste_logs:
            st.warning("⚠️ No waste data available for the selected period and filters.")
            return
        
        # Generate summary
        summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Waste", f"{summary['total_waste_kg']:.1f} kg")
        
        with col2:
            st.metric("Total Cost", f"${summary['total_cost']:.2f}")
        
        with col3:
            st.metric("Daily Average", f"{summary['daily_average']:.1f} kg")
        
        with col4:
            st.metric("Total Entries", summary['total_entries'])
        
        # Charts row 1
        col1, col2 = st.columns(2)
        
        with col1:
            fig = self.charts.create_waste_trend_chart(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = self.charts.create_category_pie_chart(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        # Charts row 2
        col1, col2 = st.columns(2)
        
        with col1:
            fig = self.charts.create_waste_type_bar_chart(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = self.charts.create_top_waste_items_chart(waste_logs, limit=8)
            st.plotly_chart(fig, use_container_width=True)
        
        # Environmental impact
        st.markdown("### 🌍 Environmental Impact")
        fig = self.charts.create_environmental_impact_chart(waste_logs)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.markdown("### 💡 Recommendations")
        recommendations = WasteLoggingHelpers.get_waste_recommendations(waste_logs)
        
        if recommendations:
            for i, rec in enumerate(recommendations[:5], 1):
                st.info(f"{i}. {rec}")
        else:
            st.info("No specific recommendations available.")
    
    def _show_meal_preparation(self):
        """Show meal preparation logging form."""
        st.markdown("## 🍳 Meal Preparation Logging")
        
        # Show form
        success = self.forms.meal_preparation_form()
        
        if success:
            st.success("✅ Meal preparation logged successfully!")
            st.experimental_rerun()
    
    def _show_leftovers(self):
        """Show leftovers logging form."""
        st.markdown("## 🥡 Leftovers Logging")
        
        # Show form
        success = self.forms.leftovers_form()
        
        if success:
            st.success("✅ Leftovers logged successfully!")
            st.experimental_rerun()
    
    def _show_disposed_food(self):
        """Show disposed food logging form."""
        st.markdown("## 🗑️ Disposed Food Logging")
        
        # Show form
        success = self.forms.disposed_food_form()
        
        if success:
            st.success("✅ Disposed food logged successfully!")
            st.experimental_rerun()
    
    def _show_serving_quantities(self):
        """Show serving quantities tracking form."""
        st.markdown("## 🍽️ Serving Quantities Tracking")
        
        # Show form
        success = self.forms.serving_quantities_form()
        
        if success:
            st.success("✅ Serving quantities logged successfully!")
            st.experimental_rerun()
    
    def _show_daily_report(self):
        """Show daily report upload form."""
        st.markdown("## 📤 Daily Waste Report Upload")
        
        # Show form
        success = self.forms.daily_report_upload_form()
        
        if success:
            st.success("✅ Daily report uploaded successfully!")
            st.experimental_rerun()
    
    def _show_data_view(self):
        """Show data view with editable table."""
        st.markdown("## 📋 Waste Data View")
        
        # Get filtered data
        waste_logs = self._get_filtered_waste_logs()
        
        if not waste_logs:
            st.warning("⚠️ No waste data available for the selected period and filters.")
            return
        
        # Create dataframe
        df = WasteLoggingHelpers.create_waste_dataframe(waste_logs)
        
        # Add edit/delete columns
        df['Actions'] = '📝 Edit | 🗑️ Delete'
        
        # Show data table
        st.markdown("### 📊 Waste Records")
        
        # Data editor
        edited_df = st.data_editor(
            df,
            column_config={
                "id": st.column_config.NumberColumn(
                    "ID",
                    help="Unique identifier",
                    disabled=True
                ),
                "food_item": st.column_config.TextColumn(
                    "Food Item",
                    help="Name of the food item",
                    width="large"
                ),
                "category": st.column_config.SelectboxColumn(
                    "Category",
                    help="Food category",
                    options=["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"]
                ),
                "waste_category": st.column_config.SelectboxColumn(
                    "Waste Category",
                    help="Type of waste",
                    options=[cat.value for cat in WasteCategory]
                ),
                "quantity_kg": st.column_config.NumberColumn(
                    "Quantity (kg)",
                    help="Weight in kilograms",
                    format="%.2f"
                ),
                "estimated_cost": st.column_config.NumberColumn(
                    "Cost ($)",
                    help="Estimated cost",
                    format="%.2f"
                ),
                "dining_hall": st.column_config.TextColumn(
                    "Dining Hall",
                    help="Location of waste"
                ),
                "meal_period": st.column_config.SelectboxColumn(
                    "Meal Period",
                    help="Meal period",
                    options=[meal.value for meal in MealType]
                ),
                "waste_date": st.column_config.DateColumn(
                    "Date",
                    help="Date of waste"
                ),
                "reason": st.column_config.TextColumn(
                    "Reason",
                    help="Reason for waste",
                    width="large"
                )
            },
            hide_index=True,
            use_container_width=True,
            height=500
        )
        
        # Export options
        st.markdown("### 📤 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export to CSV", use_container_width=True):
                filename = WasteLoggingHelpers.export_to_csv(waste_logs)
                st.success(f"✅ Data exported to {filename}")
        
        with col2:
            if st.button("📥 Export to Excel", use_container_width=True):
                filename = WasteLoggingHelpers.export_to_excel(waste_logs)
                st.success(f"✅ Data exported to {filename}")
        
        with col3:
            if st.button("📊 Generate Report", use_container_width=True):
                st.session_state.page = 'analytics'
                st.experimental_rerun()
    
    def _show_analytics(self):
        """Show comprehensive analytics page."""
        st.markdown("## 📈 Waste Analytics")
        
        # Get filtered data
        waste_logs = self._get_filtered_waste_logs()
        
        if not waste_logs:
            st.warning("⚠️ No waste data available for the selected period and filters.")
            return
        
        # Generate summary
        summary = WasteLoggingHelpers.generate_waste_summary(waste_logs)
        
        # Performance score
        score_data = WasteLoggingHelpers.calculate_waste_score(waste_logs)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig = self.charts.create_waste_score_gauge(score_data['score'], score_data['grade'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Performance Factors")
            for factor, value in score_data['factors'].items():
                factor_name = factor.replace('_', ' ').title()
                st.metric(factor_name, f"{value:.0f}/100")
        
        with col3:
            st.markdown("### 💡 Key Insights")
            insights = []
            
            if summary['daily_average'] > 50:
                insights.append("🔴 High daily waste average")
            elif summary['daily_average'] > 30:
                insights.append("🟡 Moderate daily waste average")
            else:
                insights.append("🟢 Low daily waste average")
            
            if summary['total_cost'] > 1000:
                insights.append("💰 High cost impact")
            
            top_category = max(summary['category_breakdown'].items(), key=lambda x: x[1]['quantity_kg'])
            insights.append(f"📦 {top_category[0]} is top waste category")
            
            for insight in insights:
                st.info(insight)
        
        # Detailed charts
        st.markdown("### 📊 Detailed Analysis")
        
        # Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            fig = self.charts.create_dining_hall_comparison(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = self.charts.create_meal_period_comparison(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        # Row 2
        col1, col2 = st.columns(2)
        
        with col1:
            fig = self.charts.create_cost_analysis_chart(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = self.charts.create_waste_heatmap(waste_logs)
            st.plotly_chart(fig, use_container_width=True)
        
        # Trends analysis
        st.markdown("### 📈 Trends Analysis")
        
        trends = WasteLoggingHelpers.calculate_waste_trends(waste_logs)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Trend Direction")
            trend_emoji = {"increasing": "📈", "decreasing": "📉", "stable": "➡️"}
            trend_color = {"increasing": "red", "decreasing": "green", "stable": "blue"}
            
            st.markdown(f"""
            <div style="font-size: 2rem;">
                {trend_emoji.get(trends['trend'], '➡️')} {trends['trend'].title()}
            </div>
            <div style="color: {trend_color.get(trends['trend'], 'black')};">
                Change: {trends['change_percentage']:+.1f}%
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 📋 Recommendations")
            recommendations = WasteLoggingHelpers.get_waste_recommendations(waste_logs)
            
            for i, rec in enumerate(recommendations[:3], 1):
                st.info(f"{i}. {rec}")
        
        # Export analytics
        st.markdown("### 📤 Export Analytics")
        
        if st.button("📊 Generate Full Report", use_container_width=True):
            # Generate comprehensive report
            report_data = {
                'summary': summary,
                'score': score_data,
                'trends': trends,
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
            
            # Convert to JSON and provide download
            report_json = json.dumps(report_data, indent=2, default=str)
            st.download_button(
                label="📥 Download Report (JSON)",
                data=report_json,
                file_name=f"waste_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def main():
    """Main function to run the waste logging app."""
    try:
        app = WasteLoggingApp()
        app.run()
    except Exception as e:
        logger.error(f"Error running waste logging app: {str(e)}")
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please refresh the page and try again.")


if __name__ == "__main__":
    main()
