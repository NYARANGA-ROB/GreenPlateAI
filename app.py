"""
GreenPlateAI - University Food Waste Reduction Platform
Main Streamlit application for AI-powered food waste reduction in university dining.
"""

import streamlit as st
import sys
import os
import random
from pathlib import Path
import logging
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import application modules
from utils.config import get_config, get_environment_info
from database.connection import init_db, check_database_health
from utils.helpers import format_currency, format_weight, format_percentage
from auth.authenticator import authenticate_user, logout_user, get_current_user
from dashboards.charts import create_waste_trend_chart, create_category_pie_chart

from forecasting.models import get_demand_forecast

from recommendations.engine import get_waste_reduction_recommendations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize configuration
config = get_config()

# Streamlit page configuration
st.set_page_config(
    page_title=config.app_name,
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2E8B57;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid #c3e6cb;
    }
    .warning-message {
        background: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid #ffeaa7;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False


def initialize_database():
    """Initialize database if not already done."""
    if not st.session_state.db_initialized:
        try:
            init_db()
            st.session_state.db_initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            st.error("Failed to initialize database. Please check configuration.")
            return False
    return True


def render_login_page():
    """Render the login page."""
    st.markdown('<h1 class="main-header">🥗 GreenPlateAI</h1>', unsafe_allow_html=True)
    st.markdown("### University Food Waste Reduction Platform")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("#### Sign In")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            
            submitted = st.form_submit_button("Sign In", type="primary")
            
            if submitted:
                if email and password:
                    user = authenticate_user(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(f"Welcome back, {user.full_name or user.username}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password. Please try again.")
                else:
                    st.error("Please enter both email and password.")
        
        st.markdown("---")
        st.markdown("**Demo Credentials:**")
        st.code("Email: admin@greenplateai.com\nPassword: admin123")


def render_sidebar():
    """Render the application sidebar."""
    if not st.session_state.authenticated:
        return
    
    user = st.session_state.user
    
    # User info section
    with st.sidebar:
        st.markdown(f"### 👤 {user.full_name or user.username}")
        st.markdown(f"**Role:** {user.role.title()}")
        st.markdown(f"**Email:** {user.email}")
        
        if st.button("🚪 Logout", type="secondary"):
            logout_user()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
    
    # Navigation menu
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        
        pages = [
            "📊 Dashboard",
            "📈 Analytics",
            "🤖 Forecasting", 
            "💡 Recommendations",
            "📋 Inventory",
            "📝 Data Entry",
            "📄 Reports",
            "⚙️ Settings"
        ]
        
        if user.is_admin:
            pages.extend([
                "👥 Users",
                "🔧 System"
            ])
        
        selected_page = st.selectbox(
            "Select Page",
            pages,
            index=pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0
        )
        
        st.session_state.current_page = selected_page.split(" ", 1)[1] if " " in selected_page else selected_page
    
    # Quick stats
    with st.sidebar:
        st.markdown("### 📊 Quick Stats")
        
        try:
            from models.waste_record import WasteRecord
            from database.connection import get_session
            
            db = get_session()
            
            # Today's waste
            today = date.today()
            today_waste = db.query(WasteRecord).filter(
                WasteRecord.date == today,
                WasteRecord.is_active == True
            ).all()
            
            total_waste_today = sum(record.quantity_kg for record in today_waste)
            st.metric("Today's Waste", format_weight(total_waste_today))
            
            # This week's waste
            week_start = today - timedelta(days=today.weekday())
            week_waste = db.query(WasteRecord).filter(
                WasteRecord.date >= week_start,
                WasteRecord.is_active == True
            ).all()
            
            total_waste_week = sum(record.quantity_kg for record in week_waste)
            st.metric("Week's Waste", format_weight(total_waste_week))
            
            db.close()
        except Exception as e:
            logger.error(f"Failed to load quick stats: {e}")
            st.error("Unable to load statistics")


def render_dashboard():
    """Render the main dashboard page."""
    st.markdown("## 📊 Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        from models.waste_record import WasteRecord
        from database.connection import get_session
        
        db = get_session()
        
        # Get date range for metrics
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        # Today's metrics
        today_waste = db.query(WasteRecord).filter(
            WasteRecord.date == today,
            WasteRecord.is_active == True
        ).all()
        
        total_waste_today = sum(record.quantity_kg for record in today_waste)
        total_cost_today = sum(record.estimated_cost or 0 for record in today_waste)
        
        # Week's metrics
        week_waste = db.query(WasteRecord).filter(
            WasteRecord.date >= week_start,
            WasteRecord.is_active == True
        ).all()
        
        total_waste_week = sum(record.quantity_kg for record in week_waste)
        total_cost_week = sum(record.estimated_cost or 0 for record in week_waste)
        
        # Month's metrics
        month_waste = db.query(WasteRecord).filter(
            WasteRecord.date >= month_start,
            WasteRecord.is_active == True
        ).all()
        
        total_waste_month = sum(record.quantity_kg for record in month_waste)
        total_cost_month = sum(record.estimated_cost or 0 for record in month_waste)
        
        db.close()
        
        with col1:
            st.metric(
                "Today's Waste",
                format_weight(total_waste_today),
                f"{format_currency(total_cost_today)}"
            )
        
        with col2:
            st.metric(
                "This Week",
                format_weight(total_waste_week),
                f"{format_currency(total_cost_week)}"
            )
        
        with col3:
            st.metric(
                "This Month",
                format_weight(total_waste_month),
                f"{format_currency(total_cost_month)}"
            )
        
        with col4:
            # Calculate trend
            if len(week_waste) > 0:
                avg_daily = total_waste_week / 7
                trend = ((total_waste_today - avg_daily) / avg_daily * 100) if avg_daily > 0 else 0
                st.metric(
                    "Daily Trend",
                    format_weight(total_waste_today),
                    f"{trend:+.1f}%"
                )
            else:
                st.metric("Daily Trend", "No Data")
        
    except Exception as e:
        logger.error(f"Failed to load dashboard metrics: {e}")
        st.error("Unable to load dashboard metrics")
    
    st.markdown("---")
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Waste Trend")
        try:
            fig = create_waste_trend_chart(days=30)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Failed to create waste trend chart: {e}")
            st.error("Unable to load waste trend chart")
    
    with col2:
        st.markdown("### 🥧 Waste by Category")
        try:
            fig = create_category_pie_chart(days=30)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Failed to create category chart: {e}")
            st.error("Unable to load category chart")
    
    # Recent waste records
    st.markdown("### 📋 Recent Waste Records")
    
    try:
        db = get_session()
        recent_records = db.query(WasteRecord).filter(
            WasteRecord.is_active == True
        ).order_by(WasteRecord.created_at.desc()).limit(10).all()
        
        if recent_records:
            records_data = []
            for record in recent_records:
                records_data.append({
                    "Date": record.date,
                    "Food Item": record.food_item.name if record.food_item else "Unknown",
                    "Category": record.category,
                    "Quantity": format_weight(record.quantity_kg),
                    "Cost": format_currency(record.estimated_cost or 0),
                    "Source": record.source
                })
            
            df = pd.DataFrame(records_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No waste records found. Start by adding data in the Data Entry section.")
        
        db.close()
    except Exception as e:
        logger.error(f"Failed to load recent records: {e}")
        st.error("Unable to load recent waste records")


def render_analytics():
    """Render the analytics page."""
    st.markdown("## 📈 Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("Start Date", date.today() - timedelta(days=30))
    
    with col2:
        end_date = st.date_input("End Date", date.today())
    
    if start_date > end_date:
        st.error("Start date cannot be after end date")
        return
    
    # Analytics sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Waste Analysis")
        
        try:
            from models.waste_record import WasteRecord
            from database.connection import get_session
            
            db = get_session()
            
            # Get waste data for date range
            waste_records = db.query(WasteRecord).filter(
                WasteRecord.date >= start_date,
                WasteRecord.date <= end_date,
                WasteRecord.is_active == True
            ).all()
            
            if waste_records:
                # Create analysis dataframe
                data = []
                for record in waste_records:
                    data.append({
                        'date': record.date,
                        'quantity_kg': float(record.quantity_kg),
                        'category': record.category,
                        'source': record.source,
                        'cost': float(record.estimated_cost or 0)
                    })
                
                df = pd.DataFrame(data)
                
                # Daily waste trend
                daily_df = df.groupby('date').agg({
                    'quantity_kg': 'sum',
                    'cost': 'sum'
                }).reset_index()
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=daily_df['date'],
                    y=daily_df['quantity_kg'],
                    mode='lines+markers',
                    name='Waste (kg)',
                    line=dict(color='#2E8B57')
                ))
                
                fig.update_layout(
                    title="Daily Waste Trend",
                    xaxis_title="Date",
                    yaxis_title="Waste (kg)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Category breakdown
                category_df = df.groupby('category').agg({
                    'quantity_kg': 'sum',
                    'cost': 'sum'
                }).reset_index()
                
                fig = px.pie(
                    category_df,
                    values='quantity_kg',
                    names='category',
                    title="Waste by Category"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info("No waste data found for the selected period.")
            
            db.close()
        except Exception as e:
            logger.error(f"Failed to load analytics: {e}")
            st.error("Unable to load analytics data")
    
    with col2:
        st.markdown("### 📈 Insights")
        
        try:
            # Calculate insights
            if waste_records:
                total_waste = sum(record.quantity_kg for record in waste_records)
                total_cost = sum(record.estimated_cost or 0 for record in waste_records)
                avg_daily = total_waste / ((end_date - start_date).days + 1)
                
                # Top waste categories
                category_totals = {}
                for record in waste_records:
                    category_totals[record.category] = category_totals.get(record.category, 0) + float(record.quantity_kg)
                
                top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else ("None", 0)
                
                # Display insights
                st.markdown(f"""
                **Key Metrics:**
                - **Total Waste:** {format_weight(total_waste)}
                - **Total Cost:** {format_currency(total_cost)}
                - **Daily Average:** {format_weight(avg_daily)}
                - **Top Category:** {top_category[0]} ({format_weight(top_category[1])})
                """)
                
                # Recommendations
                st.markdown("**Quick Recommendations:**")
                if top_category[0] == "overproduction":
                    st.write("• Consider reducing preparation quantities")
                elif top_category[0] == "spoilage":
                    st.write("• Review storage conditions and expiration dates")
                elif top_category[0] == "plate_waste":
                    st.write("• Analyze portion sizes and student preferences")
                else:
                    st.write("• Monitor waste patterns and identify improvement areas")
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            st.error("Unable to generate insights")


def render_forecasting():
    """Render the forecasting page."""
    st.markdown("## 🤖 Forecasting")
    
    st.markdown("### Food Demand Forecasting")
    
    # Forecast options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_days = st.selectbox("Forecast Period", [7, 14, 30], index=0)
    
    with col2:
        meal_period = st.selectbox("Meal Period", ["All", "breakfast", "lunch", "dinner"])
    
    with col3:
        dining_hall = st.selectbox("Dining Hall", ["All", "Main Hall", "West Campus", "North Campus"])
    
    if st.button("Generate Forecast", type="primary"):
        try:
            # Generate forecast
            forecast_data = get_demand_forecast(
                days_ahead=forecast_days,
                meal_period=meal_period if meal_period != "All" else None,
                dining_hall=dining_hall if dining_hall != "All" else None
            )
            
            if forecast_data:
                # Display forecast chart
                fig = go.Figure()
                
                dates = [item['date'] for item in forecast_data]
                predicted = [item['predicted_value'] for item in forecast_data]
                confidence_lower = [item.get('confidence_interval_lower', 0) for item in forecast_data]
                confidence_upper = [item.get('confidence_interval_upper', 0) for item in forecast_data]
                
                # Add confidence interval
                fig.add_trace(go.Scatter(
                    x=dates + dates[::-1],
                    y=confidence_upper + confidence_lower[::-1],
                    fill='toself',
                    fillcolor='rgba(46, 139, 87, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='Confidence Interval'
                ))
                
                # Add predicted values
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=predicted,
                    mode='lines+markers',
                    name='Predicted Demand',
                    line=dict(color='#2E8B57', width=3)
                ))
                
                fig.update_layout(
                    title=f"Food Demand Forecast - Next {forecast_days} Days",
                    xaxis_title="Date",
                    yaxis_title="Predicted Demand (kg)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display forecast table
                st.markdown("### Forecast Details")
                
                forecast_df = pd.DataFrame(forecast_data)
                forecast_df['date'] = pd.to_datetime(forecast_df['date']).dt.date
                forecast_df['predicted_value'] = forecast_df['predicted_value'].round(2)
                forecast_df['confidence_score'] = forecast_df['confidence_score'].round(3)
                
                st.dataframe(forecast_df, use_container_width=True)
                
            else:
                st.warning("Unable to generate forecast. Please ensure you have sufficient historical data.")
        
        except Exception as e:
            logger.error(f"Failed to generate forecast: {e}")
            st.error("Failed to generate forecast. Please try again.")


def render_recommendations():
    """Render the recommendations page."""
    st.markdown("## 💡 Recommendations")
    
    # Recommendation filters
    col1, col2 = st.columns(2)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "Preparation", "Spoilage", "Overproduction", "Plate Waste"]
        )
    
    with col2:
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "High", "Medium", "Low"]
        )
    
    if st.button("Get Recommendations", type="primary"):
        try:
            recommendations = get_waste_reduction_recommendations(
                category=category_filter if category_filter != "All" else None,
                priority=priority_filter if priority_filter != "All" else None
            )
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"{i}. {rec['title']}", expanded=i <= 3):
                        st.markdown(f"**Category:** {rec['category']}")
                        st.markdown(f"**Priority:** {rec['priority']}")
                        st.markdown(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.markdown(f"**Description:** {rec['description']}")
                        
                        if 'action_steps' in rec:
                            st.markdown("**Action Steps:**")
                            for step in rec['action_steps']:
                                st.write(f"• {step}")
                        
                        if rec.get('potential_savings'):
                            st.markdown(f"**Potential Savings:** {format_currency(rec['potential_savings'])}")
            else:
                st.info("No recommendations available at this time.")
        
        except Exception as e:
            logger.error(f"Failed to load recommendations: {e}")
            st.error("Unable to load recommendations")


def render_data_entry():
    """Render the data entry page."""
    st.markdown("## 📝 Data Entry")
    
    tab1, tab2 = st.tabs(["Waste Records", "Inventory"])
    
    with tab1:
        st.markdown("### Add Waste Record")
        
        with st.form("waste_record_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                record_date = st.date_input("Date", date.today())
                meal_period = st.selectbox("Meal Period", ["breakfast", "lunch", "dinner", "snack"])
                dining_hall = st.text_input("Dining Hall", placeholder="e.g., Main Hall")
            
            with col2:
                category = st.selectbox("Category", [
                    "preparation", "spoilage", "overproduction", 
                    "plate_waste", "expired", "damaged", "other"
                ])
                source = st.selectbox("Source", [
                    "kitchen", "dining_hall", "catering", "storage", "other"
                ])
            
            food_item = st.text_input("Food Item", placeholder="e.g., Rice, Chicken, Vegetables")
            quantity_kg = st.number_input("Quantity (kg)", min_value=0.0, step=0.1)
            estimated_cost = st.number_input("Estimated Cost ($)", min_value=0.0, step=0.01)
            notes = st.text_area("Notes (Optional)", placeholder="Additional information...")
            
            submitted = st.form_submit_button("Add Record", type="primary")
            
            if submitted:
                if food_item and quantity_kg > 0:
                    db = None
                    try:
                        from models.waste_record import WasteRecord
                        from models.food_item import FoodItem, FoodCategory
                        from database.connection import get_session
                        
                        db = get_session()

                        # Resolve food item (create one if missing) to satisfy FK constraints.
                        food_item_obj = db.query(FoodItem).filter(
                            FoodItem.name == food_item
                        ).first()

                        if food_item_obj is None:
                            default_category = db.query(FoodCategory).filter(
                                FoodCategory.name == "Uncategorized"
                            ).first()
                            if default_category is None:
                                default_category = FoodCategory(
                                    name="Uncategorized",
                                    description="Auto-created fallback category"
                                )
                                db.add(default_category)
                                db.flush()

                            food_item_obj = FoodItem(
                                name=food_item,
                                category_id=default_category.id,
                                unit_of_measure="kg"
                            )
                            db.add(food_item_obj)
                            db.flush()
                        
                        # Create waste record
                        waste_record = WasteRecord(
                            date=record_date,
                            food_item_id=food_item_obj.id,
                            category=category,
                            source=source,
                            quantity_kg=quantity_kg,
                            estimated_cost=estimated_cost,
                            meal_period=meal_period,
                            dining_hall=dining_hall,
                            notes=notes,
                            recorded_by=st.session_state.user.id if st.session_state.user else None
                        )
                        
                        db.add(waste_record)
                        db.commit()
                        
                        st.success("Waste record added successfully!")
                        st.rerun()
                    
                    except Exception as e:
                        if db is not None:
                            db.rollback()
                        logger.error(f"Failed to add waste record: {e}")
                        st.error("Failed to add waste record. Please try again.")
                    finally:
                        if db is not None:
                            db.close()
                else:
                    st.error("Please fill in all required fields.")
    
    with tab2:
        st.markdown("### Add Inventory Item")
        
        with st.form("inventory_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                food_item = st.text_input("Food Item", placeholder="e.g., Rice")
                quantity = st.number_input("Quantity", min_value=0, step=1)
                unit = st.selectbox("Unit", ["kg", "pieces", "liters", "boxes"])
            
            with col2:
                received_date = st.date_input("Received Date", date.today())
                expiration_date = st.date_input("Expiration Date")
                storage_location = st.text_input("Storage Location", placeholder="e.g., Freezer #1")
            
            batch_number = st.text_input("Batch Number (Optional)")
            cost_per_unit = st.number_input("Cost per Unit ($)", min_value=0.0, step=0.01)
            notes = st.text_area("Notes (Optional)")
            
            submitted = st.form_submit_button("Add Inventory", type="primary")
            
            if submitted:
                if food_item and quantity > 0:
                    try:
                        from models.inventory import Inventory
                        from database.connection import get_session
                        
                        db = get_session()
                        
                        inventory_item = Inventory(
                            food_item_id=1,  # Default food item ID
                            quantity=quantity,
                            batch_number=batch_number,
                            received_date=received_date,
                            expiration_date=expiration_date,
                            storage_location=storage_location,
                            cost_per_unit=cost_per_unit,
                            notes=notes
                        )
                        
                        db.add(inventory_item)
                        db.commit()
                        db.close()
                        
                        st.success("Inventory item added successfully!")
                        st.rerun()
                    
                    except Exception as e:
                        logger.error(f"Failed to add inventory item: {e}")
                        st.error("Failed to add inventory item. Please try again.")
                else:
                    st.error("Please fill in all required fields.")


def render_settings():
    """Render the settings page."""
    st.markdown("## ⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["Profile", "System", "Data"])
    
    with tab1:
        st.markdown("### User Profile")
        
        if st.session_state.user:
            user = st.session_state.user
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Name:** {user.full_name or 'Not set'}")
                st.markdown(f"**Email:** {user.email}")
                st.markdown(f"**Username:** {user.username}")
                st.markdown(f"**Role:** {user.role.title()}")
            
            with col2:
                st.markdown(f"**Department:** {user.department or 'Not set'}")
                st.markdown(f"**Phone:** {user.phone or 'Not set'}")
                st.markdown(f"**Last Login:** {user.last_login or 'Never'}")
            
            st.markdown("---")
            st.markdown("### Change Password")
            
            with st.form("change_password"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                submitted = st.form_submit_button("Change Password", type="primary")
                
                if submitted:
                    if current_password and new_password and confirm_password:
                        if new_password == confirm_password:
                            # Password change logic would go here
                            st.success("Password changed successfully!")
                        else:
                            st.error("New passwords do not match.")
                    else:
                        st.error("Please fill in all fields.")
    
    with tab2:
        st.markdown("### System Information")
        
        env_info = get_environment_info()
        
        st.markdown(f"**Application:** {env_info['app_name']} v{env_info['app_version']}")
        st.markdown(f"**Environment:** {env_info['environment']}")
        st.markdown(f"**Database:** {env_info['database_url']}")
        st.markdown(f"**Timezone:** {env_info['timezone']}")
        
        st.markdown("---")
        st.markdown("### Database Health")
        
        try:
            health = check_database_health()
            
            if health['status'] == 'healthy':
                st.success("✅ Database is healthy")
            else:
                st.error(f"❌ Database issue: {health.get('error', 'Unknown')}")
            
            if 'pool_size' in health:
                st.markdown(f"**Connection Pool Size:** {health['pool_size']}")
        
        except Exception as e:
            st.error(f"Failed to check database health: {e}")
    
    with tab3:
        st.markdown("### Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All Data", type="secondary"):
                try:
                    # Export logic would go here
                    st.success("Data export initiated!")
                except Exception as e:
                    st.error("Failed to export data")
        
        with col2:
            if st.button("Import Data", type="secondary"):
                uploaded_file = st.file_uploader(
                    "Choose a file",
                    type=['csv', 'xlsx'],
                    help="Upload CSV or Excel file with waste data"
                )
                
                if uploaded_file:
                    # Import logic would go here
                    st.success("Data imported successfully!")


def seed_demo_data(days: int = 21, records_per_day: int = 4) -> int:
    """Insert demo food items and waste records for visualization/testing."""
    from database.connection import get_session
    from models.food_item import FoodCategory, FoodItem
    from models.waste_record import WasteRecord
    from models.user import User

    db = get_session()
    inserted = 0
    try:
        category_map = {
            "Vegetables": "Fresh and cooked vegetables",
            "Proteins": "Meat, fish, eggs and legumes",
            "Carbohydrates": "Rice, pasta and grains",
            "Dairy": "Milk, cheese and yogurt",
            "Fruits": "Fresh fruits and fruit salads",
        }
        categories = {}
        for name, description in category_map.items():
            category = db.query(FoodCategory).filter(FoodCategory.name == name).first()
            if category is None:
                category = FoodCategory(name=name, description=description)
                db.add(category)
                db.flush()
            categories[name] = category

        food_catalog = [
            ("Rice", "Carbohydrates"),
            ("Chicken", "Proteins"),
            ("Beans", "Proteins"),
            ("Potatoes", "Carbohydrates"),
            ("Spinach", "Vegetables"),
            ("Carrots", "Vegetables"),
            ("Milk", "Dairy"),
            ("Bananas", "Fruits"),
        ]

        food_items = []
        for food_name, category_name in food_catalog:
            item = db.query(FoodItem).filter(FoodItem.name == food_name).first()
            if item is None:
                item = FoodItem(
                    name=food_name,
                    category_id=categories[category_name].id,
                    unit_of_measure="kg",
                    cost_per_unit=round(random.uniform(0.4, 3.0), 2),
                )
                db.add(item)
                db.flush()
            food_items.append(item)

        user = db.query(User).filter(User.is_active == True).order_by(User.id.asc()).first()
        recorded_by = str(user.id) if user else None

        sources = ["kitchen", "dining_hall", "storage", "catering"]
        meal_periods = ["breakfast", "lunch", "dinner", "snack"]
        dining_halls = ["Main Hall", "Nairobi", "Science Campus", "Residence Block A"]
        categories_for_records = [
            "preparation", "spoilage", "overproduction", "plate_waste", "expired", "damaged"
        ]

        for day_offset in range(days):
            record_date = date.today() - timedelta(days=day_offset)
            for _ in range(records_per_day):
                item = random.choice(food_items)
                quantity = round(random.uniform(0.5, 15.0), 2)
                unit_cost = float(item.cost_per_unit or 1.2)
                estimated_cost = round(quantity * unit_cost * random.uniform(0.8, 1.3), 2)

                db.add(WasteRecord(
                    date=record_date,
                    food_item_id=item.id,
                    category=random.choice(categories_for_records),
                    source=random.choice(sources),
                    quantity_kg=quantity,
                    estimated_cost=estimated_cost,
                    meal_period=random.choice(meal_periods),
                    dining_hall=random.choice(dining_halls),
                    recorded_by=recorded_by,
                    notes="Demo seeded data"
                ))
                inserted += 1

        db.commit()
        return inserted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def render_users_page():
    """Render user administration page."""
    st.markdown("## 👥 Users")

    current_user = st.session_state.user
    if not current_user or not current_user.is_admin:
        st.warning("Only administrators can access the Users page.")
        return

    from database.connection import get_session
    from models.user import User, UserRole
    from auth.authenticator import create_user, update_user, delete_user

    with st.expander("➕ Create User", expanded=False):
        with st.form("create_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                full_name = st.text_input("Full Name")
                email = st.text_input("Email")
                username = st.text_input("Username")
            with col2:
                department = st.text_input("Department")
                phone = st.text_input("Phone")
                role = st.selectbox("Role", [r.value for r in UserRole], index=3)
            password = st.text_input("Temporary Password", type="password")
            submitted = st.form_submit_button("Create User", type="primary")

            if submitted:
                if not email or not username or not password:
                    st.error("Email, username, and password are required.")
                else:
                    new_user = create_user(
                        email=email,
                        username=username,
                        password=password,
                        role=role,
                        full_name=full_name,
                        department=department,
                        phone=phone
                    )
                    if new_user:
                        st.success(f"User created: {new_user.email}")
                        st.rerun()
                    else:
                        st.error("Failed to create user. Email or username may already exist.")

    db = get_session()
    try:
        users = db.query(User).order_by(User.created_at.desc()).all()
        if not users:
            st.info("No users found.")
            return

        summary = pd.DataFrame([
            {
                "ID": u.id,
                "Name": u.full_name or "",
                "Email": u.email,
                "Username": u.username,
                "Role": str(u.role),
                "Active": bool(u.is_active),
                "Last Login": u.last_login,
                "Logins": int(u.login_count or 0),
            }
            for u in users
        ])
        st.dataframe(summary, use_container_width=True)

        selected_user_id = st.selectbox(
            "Select user to manage",
            [u.id for u in users],
            format_func=lambda uid: next(
                (f"{u.full_name or u.username} ({u.email})" for u in users if u.id == uid),
                str(uid)
            )
        )
    finally:
        db.close()

    selected_user = next((u for u in users if u.id == selected_user_id), None)
    if selected_user is None:
        return

    with st.expander("✏️ Edit Selected User", expanded=True):
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Full Name", value=selected_user.full_name or "")
                new_email = st.text_input("Email", value=selected_user.email or "")
                new_username = st.text_input("Username", value=selected_user.username or "")
            with col2:
                new_department = st.text_input("Department", value=selected_user.department or "")
                new_phone = st.text_input("Phone", value=selected_user.phone or "")
                role_options = [r.value for r in UserRole]
                role_index = role_options.index(str(selected_user.role)) if str(selected_user.role) in role_options else 3
                new_role = st.selectbox("Role", role_options, index=role_index)

            col_update, col_toggle, col_delete = st.columns(3)
            update_clicked = col_update.form_submit_button("Update User", type="primary")
            toggle_label = "Deactivate User" if selected_user.is_active else "Reactivate User"
            toggle_clicked = col_toggle.form_submit_button(toggle_label)
            delete_clicked = col_delete.form_submit_button("Soft Delete User")

        if update_clicked:
            updated = update_user(
                user_id=selected_user.id,
                email=new_email,
                username=new_username,
                full_name=new_name,
                department=new_department,
                phone=new_phone,
                role=new_role
            )
            if updated:
                st.success("User updated successfully.")
                st.rerun()
            else:
                st.error("Failed to update user. Check duplicate email/username.")

        if toggle_clicked:
            db = get_session()
            try:
                target = db.query(User).filter(User.id == selected_user.id).first()
                if target:
                    target.is_active = not bool(target.is_active)
                    db.commit()
                    st.success("User status updated.")
                    st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"Failed to update user status: {e}")
            finally:
                db.close()

        if delete_clicked:
            if str(selected_user.id) == str(current_user.id):
                st.error("You cannot delete your own active account.")
            elif delete_user(selected_user.id):
                st.success("User soft-deleted.")
                st.rerun()
            else:
                st.error("Failed to delete user.")


def render_system_page():
    """Render system administration page."""
    st.markdown("## 🔧 System")

    current_user = st.session_state.user
    if not current_user or not current_user.is_admin:
        st.warning("Only administrators can access the System page.")
        return

    env_info = get_environment_info()
    health = check_database_health()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Environment", env_info["environment"].title())
    with col2:
        st.metric("Database", health.get("status", "unknown").title())
    with col3:
        st.metric("App Version", env_info["app_version"])

    st.markdown("### Environment Info")
    st.json(env_info)

    from database.connection import get_session
    from models.user import User, Session
    from models.food_item import FoodItem, FoodCategory, Inventory
    from models.waste_record import WasteRecord
    from models.prediction import Prediction, PredictionModel

    db = get_session()
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        active_sessions = db.query(Session).filter(Session.is_active == True).count()
        total_food_items = db.query(FoodItem).count()
        total_categories = db.query(FoodCategory).count()
        total_inventory = db.query(Inventory).count()
        total_waste_records = db.query(WasteRecord).count()
        total_predictions = db.query(Prediction).count()
        total_models = db.query(PredictionModel).count()
    finally:
        db.close()

    st.markdown("### Data Overview")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Users", total_users)
    metric_cols[1].metric("Active Users", active_users)
    metric_cols[2].metric("Active Sessions", active_sessions)
    metric_cols[3].metric("Waste Records", total_waste_records)

    metric_cols2 = st.columns(4)
    metric_cols2[0].metric("Food Items", total_food_items)
    metric_cols2[1].metric("Categories", total_categories)
    metric_cols2[2].metric("Inventory Rows", total_inventory)
    metric_cols2[3].metric("Predictions", total_predictions)
    st.caption(f"Registered prediction models: {total_models}")

    st.markdown("### Admin Actions")
    action_col1, action_col2 = st.columns(2)

    with action_col1:
        if st.button("Seed Demo Data (21 days)", type="primary"):
            try:
                inserted = seed_demo_data(days=21, records_per_day=4)
                st.success(f"Inserted {inserted} demo waste records.")
                st.rerun()
            except Exception as e:
                logger.error(f"Failed to seed demo data: {e}")
                st.error(f"Failed to seed demo data: {e}")

    with action_col2:
        if st.button("Refresh System Stats"):
            st.rerun()


def main():
    """Main application entry point."""
    # Initialize session state
    initialize_session_state()
    
    # Initialize database
    if not initialize_database():
        st.error("Application failed to start. Database initialization failed.")
        return
    
    # Render login page or main app
    if not st.session_state.authenticated:
        render_login_page()
    else:
        # Render sidebar
        render_sidebar()
        
        # Render main content based on selected page
        page = st.session_state.current_page
        
        if page == "Dashboard":
            render_dashboard()
        elif page == "Analytics":
            render_analytics()
        elif page == "Forecasting":
            render_forecasting()
        elif page == "Recommendations":
            render_recommendations()
        elif page == "Data Entry":
            render_data_entry()
        elif page == "Users":
            render_users_page()
        elif page == "System":
            render_system_page()
        elif page == "Settings":
            render_settings()
        else:
            # Placeholder for other pages
            st.markdown(f"## {page}")
            st.info("This page is under development.")


if __name__ == "__main__":
    main()
