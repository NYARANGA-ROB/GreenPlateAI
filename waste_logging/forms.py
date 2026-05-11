"""
Streamlit forms for Food Waste Logging module.

This module provides user-friendly forms for logging meal preparation,
leftovers, disposed food, serving quantities, and daily reports.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging

from database.connection import get_session
from database.models import MealType, WasteCategory
from waste_logging.database_ops import WasteLoggingDB
from waste_logging.validators import (
    validate_meal_preparation_data,
    validate_leftovers_data,
    validate_disposed_food_data,
    validate_serving_quantities_data,
    validate_daily_report_data
)

logger = logging.getLogger(__name__)


class WasteLoggingForms:
    """Streamlit forms for waste logging operations."""
    
    def __init__(self):
        """Initialize forms with database session."""
        self.session = get_session()
        self.db_ops = WasteLoggingDB(self.session)
    
    def meal_preparation_form(self) -> bool:
        """Display meal preparation logging form."""
        st.markdown("### 🍳 Meal Preparation Logging")
        st.markdown("Log meal preparation details to track potential waste.")
        
        with st.form("meal_preparation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dining_hall = st.selectbox(
                    "Dining Hall*",
                    options=self._get_dining_halls(),
                    key="meal_prep_dining_hall",
                    help="Select the dining hall where meals were prepared"
                )
                
                meal_type = st.selectbox(
                    "Meal Type*",
                    options=[meal_type.value for meal_type in MealType],
                    key="meal_prep_type",
                    help="Select the meal period"
                )
            
            with col2:
                preparation_date = st.date_input(
                    "Preparation Date*",
                    value=date.today(),
                    max_value=date.today(),
                    key="meal_prep_date",
                    help="Date when meals were prepared"
                )
                
                meal_shift = st.selectbox(
                    "Meal Shift",
                    options=["Morning", "Afternoon", "Evening", "Night"],
                    key="meal_prep_shift",
                    help="Select the meal preparation shift"
                )
            
            st.markdown("#### 🥘 Food Items Prepared")
            
            # Dynamic food items input
            num_items = st.number_input(
                "Number of Food Items",
                min_value=1,
                max_value=20,
                value=3,
                key="num_food_items",
                help="Number of different food items prepared"
            )
            
            food_items = []
            
            for i in range(num_items):
                st.markdown(f"**Food Item {i+1}**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    food_name = st.text_input(
                        "Food Name*",
                        key=f"food_name_{i}",
                        placeholder=f"e.g., Chicken Curry"
                    )
                
                with col2:
                    category = st.selectbox(
                        "Category*",
                        options=["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"],
                        key=f"category_{i}"
                    )
                
                with col3:
                    quantity_prepared = st.number_input(
                        "Quantity Prepared (kg)*",
                        min_value=0.01,
                        step=0.01,
                        format="%.2f",
                        key=f"quantity_prepared_{i}",
                        help="Total quantity prepared in kilograms"
                    )
                
                with col4:
                    estimated_servings = st.number_input(
                        "Estimated Servings*",
                        min_value=1,
                        key=f"estimated_servings_{i}",
                        help="Number of servings expected"
                    )
                
                if food_name and category and quantity_prepared > 0 and estimated_servings > 0:
                    food_items.append({
                        'food_name': food_name,
                        'category': category,
                        'quantity_prepared': quantity_prepared,
                        'estimated_servings': estimated_servings,
                        'meal_shift': meal_shift
                    })
            
            st.markdown("#### 📋 Additional Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                preparation_method = st.selectbox(
                    "Preparation Method",
                    options=["Standard", "Batch Cooking", "À la Carte", "Buffet", "Catering"],
                    key="preparation_method"
                )
                
                chef_name = st.text_input(
                    "Chef/Staff Name",
                    key="chef_name",
                    help="Name of the chef or staff responsible"
                )
            
            with col2:
                preparation_notes = st.text_area(
                    "Preparation Notes",
                    key="preparation_notes",
                    help="Any special notes about the preparation process",
                    height=100
                )
                
                quality_check = st.checkbox(
                    "Quality Check Completed",
                    key="quality_check",
                    help="Indicates if quality check was performed"
                )
            
            # Submit button
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button(
                    "📝 Log Meal Preparation",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Reset Form", use_container_width=True):
                    st.experimental_rerun()
            
            if submitted:
                return self._process_meal_preparation(
                    dining_hall, meal_type, preparation_date, food_items,
                    preparation_method, chef_name, preparation_notes, quality_check
                )
        
        return False
    
    def leftovers_form(self) -> bool:
        """Display leftovers logging form."""
        st.markdown("### 🥡 Leftovers Logging")
        st.markdown("Log leftover food items after meal service.")
        
        with st.form("leftovers_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dining_hall = st.selectbox(
                    "Dining Hall*",
                    options=self._get_dining_halls(),
                    key="leftovers_dining_hall"
                )
                
                meal_type = st.selectbox(
                    "Meal Type*",
                    options=[meal_type.value for meal_type in MealType],
                    key="leftovers_meal_type"
                )
            
            with col2:
                leftovers_date = st.date_input(
                    "Leftovers Date*",
                    value=date.today(),
                    max_value=date.today(),
                    key="leftovers_date"
                )
                
                service_period = st.selectbox(
                    "Service Period",
                    options=["Breakfast", "Lunch", "Dinner", "Snack"],
                    key="service_period"
                )
            
            st.markdown("#### 🥡 Leftover Items")
            
            num_leftover_items = st.number_input(
                "Number of Leftover Items",
                min_value=1,
                max_value=15,
                value=2,
                key="num_leftover_items"
            )
            
            leftover_items = []
            
            for i in range(num_leftover_items):
                st.markdown(f"**Leftover Item {i+1}**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    food_item = st.text_input(
                        "Food Item*",
                        key=f"leftover_food_{i}",
                        placeholder="e.g., Rice"
                    )
                
                with col2:
                    category = st.selectbox(
                        "Category*",
                        options=["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"],
                        key=f"leftover_category_{i}"
                    )
                
                with col3:
                    quantity_kg = st.number_input(
                        "Quantity (kg)*",
                        min_value=0.01,
                        step=0.01,
                        format="%.2f",
                        key=f"leftover_quantity_{i}"
                    )
                
                with col4:
                    estimated_cost = st.number_input(
                        "Estimated Cost ($)",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key=f"leftover_cost_{i}"
                    )
                
                if food_item and category and quantity_kg > 0:
                    leftover_items.append({
                        'food_item': food_item,
                        'category': category,
                        'quantity_kg': quantity_kg,
                        'estimated_cost': estimated_cost
                    })
            
            st.markdown("#### 📦 Storage Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                storage_conditions = st.selectbox(
                    "Storage Conditions*",
                    options=["Refrigerated", "Frozen", "Room Temperature", "Hot Holding", "Other"],
                    key="storage_conditions"
                )
                
                storage_location = st.text_input(
                    "Storage Location",
                    key="storage_location",
                    placeholder="e.g., Walk-in Cooler #1"
                )
            
            with col2:
                shelf_life_hours = st.number_input(
                    "Estimated Shelf Life (hours)",
                    min_value=1,
                    max_value=168,
                    value=24,
                    key="shelf_life_hours",
                    help="How long can this be stored safely"
                )
                
                reuse_potential = st.selectbox(
                    "Reuse Potential",
                    options=["High", "Medium", "Low", "None"],
                    key="reuse_potential"
                )
            
            st.markdown("#### 📝 Additional Details")
            
            leftovers_reason = st.text_area(
                "Reason for Leftovers",
                key="leftovers_reason",
                help="Why were these items left over?",
                height=100
            )
            
            recorded_by = st.text_input(
                "Recorded By*",
                key="leftovers_recorded_by",
                help="Name of staff recording this entry"
            )
            
            # Submit button
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button(
                    "📝 Log Leftovers",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Reset Form", use_container_width=True):
                    st.experimental_rerun()
            
            if submitted:
                return self._process_leftovers(
                    dining_hall, meal_type, leftovers_date, service_period,
                    leftover_items, storage_conditions, storage_location,
                    shelf_life_hours, reuse_potential, leftovers_reason, recorded_by
                )
        
        return False
    
    def disposed_food_form(self) -> bool:
        """Display disposed food logging form."""
        st.markdown("### 🗑️ Disposed Food Logging")
        st.markdown("Log food items that were disposed of as waste.")
        
        with st.form("disposed_food_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dining_hall = st.selectbox(
                    "Dining Hall*",
                    options=self._get_dining_halls(),
                    key="disposed_dining_hall"
                )
                
                disposal_date = st.date_input(
                    "Disposal Date*",
                    value=date.today(),
                    max_value=date.today(),
                    key="disposal_date"
                )
            
            with col2:
                disposal_time = st.time_input(
                    "Disposal Time",
                    value=datetime.now().time(),
                    key="disposal_time"
                )
                
                disposal_method = st.selectbox(
                    "Disposal Method*",
                    options=["Compost", "Landfill", "Animal Feed", "Food Donation", "Other"],
                    key="disposal_method"
                )
            
            st.markdown("#### 🗑️ Disposed Items")
            
            num_disposed_items = st.number_input(
                "Number of Disposed Items",
                min_value=1,
                max_value=20,
                value=3,
                key="num_disposed_items"
            )
            
            disposed_items = []
            
            for i in range(num_disposed_items):
                st.markdown(f"**Disposed Item {i+1}**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    food_item = st.text_input(
                        "Food Item*",
                        key=f"disposed_food_{i}",
                        placeholder="e.g., Expired Vegetables"
                    )
                
                with col2:
                    category = st.selectbox(
                        "Category*",
                        options=["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"],
                        key=f"disposed_category_{i}"
                    )
                
                with col3:
                    waste_category = st.selectbox(
                        "Waste Category*",
                        options=[cat.value for cat in WasteCategory],
                        key=f"waste_category_{i}"
                    )
                
                with col4:
                    quantity_kg = st.number_input(
                        "Quantity (kg)*",
                        min_value=0.01,
                        step=0.01,
                        format="%.2f",
                        key=f"disposed_quantity_{i}"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    estimated_cost = st.number_input(
                        "Estimated Cost ($)",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key=f"disposed_cost_{i}"
                    )
                
                with col2:
                    temperature = st.number_input(
                        "Temperature (°C)",
                        value=4.0,
                        key=f"temperature_{i}",
                        help="Temperature at time of disposal"
                    )
                
                if food_item and category and waste_category and quantity_kg > 0:
                    disposed_items.append({
                        'food_item': food_item,
                        'category': category,
                        'waste_category': WasteCategory(waste_category),
                        'quantity_kg': quantity_kg,
                        'estimated_cost': estimated_cost,
                        'temperature': temperature
                    })
            
            st.markdown("#### 📋 Disposal Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                disposal_reason = st.text_area(
                    "Disposal Reason*",
                    key="disposal_reason",
                    help="Why was this food disposed?",
                    height=100
                )
                
                quality_rating = st.slider(
                    "Food Quality Rating",
                    min_value=1,
                    max_value=5,
                    value=3,
                    key="quality_rating",
                    help="1=Poor, 5=Excellent"
                )
            
            with col2:
                staff_responsible = st.text_input(
                    "Staff Responsible*",
                    key="staff_responsible",
                    help="Name of staff responsible for disposal"
                )
                
                witness_name = st.text_input(
                    "Witness Name",
                    key="witness_name",
                    help="Name of witness (if applicable)"
                )
            
            # Submit button
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button(
                    "📝 Log Disposed Food",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Reset Form", use_container_width=True):
                    st.experimental_rerun()
            
            if submitted:
                return self._process_disposed_food(
                    dining_hall, disposal_date, disposal_time, disposal_method,
                    disposed_items, disposal_reason, quality_rating,
                    staff_responsible, witness_name
                )
        
        return False
    
    def serving_quantities_form(self) -> bool:
        """Display serving quantities tracking form."""
        st.markdown("### 🍽️ Serving Quantities Tracking")
        st.markdown("Track serving quantities to identify waste patterns.")
        
        with st.form("serving_quantities_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dining_hall = st.selectbox(
                    "Dining Hall*",
                    options=self._get_dining_halls(),
                    key="serving_dining_hall"
                )
                
                meal_type = st.selectbox(
                    "Meal Type*",
                    options=[meal_type.value for meal_type in MealType],
                    key="serving_meal_type"
                )
            
            with col2:
                service_date = st.date_input(
                    "Service Date*",
                    value=date.today(),
                    max_value=date.today(),
                    key="serving_date"
                )
                
                expected_students = st.number_input(
                    "Expected Students",
                    min_value=1,
                    value=100,
                    key="expected_students",
                    help="Expected number of students"
                )
            
            st.markdown("#### 🍽️ Serving Data")
            
            num_serving_items = st.number_input(
                "Number of Menu Items",
                min_value=1,
                max_value=15,
                value=4,
                key="num_serving_items"
            )
            
            serving_data = []
            
            for i in range(num_serving_items):
                st.markdown(f"**Menu Item {i+1}**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    food_item = st.text_input(
                        "Food Item*",
                        key=f"serving_food_{i}",
                        placeholder="e.g., Chicken Stir-fry"
                    )
                
                with col2:
                    category = st.selectbox(
                        "Category*",
                        options=["Main Dish", "Side Dish", "Salad", "Dessert", "Beverage", "Other"],
                        key=f"serving_category_{i}"
                    )
                
                with col3:
                    servings_prepared = st.number_input(
                        "Servings Prepared*",
                        min_value=1,
                        key=f"serving_prepared_{i}"
                    )
                
                with col4:
                    servings_served = st.number_input(
                        "Servings Served*",
                        min_value=0,
                        key=f"serving_served_{i}"
                    )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    serving_size_kg = st.number_input(
                        "Serving Size (kg)",
                        min_value=0.01,
                        step=0.01,
                        format="%.3f",
                        key=f"serving_size_{i}",
                        help="Weight of one serving"
                    )
                
                with col2:
                    price_per_serving = st.number_input(
                        "Price per Serving ($)",
                        min_value=0.0,
                        step=0.01,
                        format="%.2f",
                        key=f"price_per_serving_{i}"
                    )
                
                if food_item and category and servings_prepared > 0:
                    waste_servings = max(0, servings_prepared - servings_served)
                    waste_kg = waste_servings * serving_size_kg
                    
                    serving_data.append({
                        'food_item': food_item,
                        'category': category,
                        'servings_prepared': servings_prepared,
                        'servings_served': servings_served,
                        'waste_servings': waste_servings,
                        'serving_size_kg': serving_size_kg,
                        'waste_kg': waste_kg,
                        'price_per_serving': price_per_serving
                    })
            
            st.markdown("#### 📊 Service Summary")
            
            # Calculate totals
            total_prepared = sum(item['servings_prepared'] for item in serving_data)
            total_served = sum(item['servings_served'] for item in serving_data)
            total_waste_servings = sum(item['waste_servings'] for item in serving_data)
            total_waste_kg = sum(item['waste_kg'] for item in serving_data)
            total_revenue = sum(item['servings_served'] * item.get('price_per_serving', 0) for item in serving_data)
            potential_revenue = sum(item['servings_prepared'] * item.get('price_per_serving', 0) for item in serving_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Prepared", f"{total_prepared}")
                st.metric("Total Served", f"{total_served}")
                st.metric("Waste Servings", f"{total_waste_servings}")
            
            with col2:
                st.metric("Waste (kg)", f"{total_waste_kg:.2f}")
                st.metric("Revenue", f"${total_revenue:.2f}")
                st.metric("Potential Revenue", f"${potential_revenue:.2f}")
            
            st.markdown("#### 📝 Additional Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                service_notes = st.text_area(
                    "Service Notes",
                    key="service_notes",
                    help="Any notes about the service",
                    height=100
                )
                
                weather_conditions = st.selectbox(
                    "Weather Conditions",
                    options=["Sunny", "Cloudy", "Rainy", "Snowy", "Other"],
                    key="weather_conditions"
                )
            
            with col2:
                special_events = st.text_input(
                    "Special Events",
                    key="special_events",
                    help="Any special events that affected service"
                )
                
                staff_supervisor = st.text_input(
                    "Staff Supervisor",
                    key="staff_supervisor",
                    help="Name of supervising staff"
                )
            
            # Submit button
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button(
                    "📝 Log Serving Quantities",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Reset Form", use_container_width=True):
                    st.experimental_rerun()
            
            if submitted:
                return self._process_serving_quantities(
                    dining_hall, meal_type, service_date, expected_students,
                    serving_data, service_notes, weather_conditions,
                    special_events, staff_supervisor
                )
        
        return False
    
    def daily_report_upload_form(self) -> bool:
        """Display daily waste report upload form."""
        st.markdown("### 📤 Daily Waste Report Upload")
        st.markdown("Upload a comprehensive daily waste report.")
        
        with st.form("daily_report_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dining_hall = st.selectbox(
                    "Dining Hall*",
                    options=self._get_dining_halls(),
                    key="report_dining_hall"
                )
                
                report_date = st.date_input(
                    "Report Date*",
                    value=date.today(),
                    max_value=date.today(),
                    key="report_date"
                )
            
            with col2:
                report_type = st.selectbox(
                    "Report Type",
                    options=["Manual Entry", "CSV Upload", "Excel Upload"],
                    key="report_type"
                )
                
                staff_prepared_by = st.text_input(
                    "Prepared By*",
                    key="staff_prepared_by",
                    help="Name of staff preparing the report"
                )
            
            if report_type == "Manual Entry":
                st.markdown("#### 📝 Manual Report Entry")
                
                num_entries = st.number_input(
                    "Number of Waste Entries",
                    min_value=1,
                    max_value=20,
                    value=5,
                    key="num_report_entries"
                )
                
                waste_entries = []
                
                for i in range(num_entries):
                    st.markdown(f"**Waste Entry {i+1}**")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        food_item = st.text_input(
                            "Food Item*",
                            key=f"report_food_{i}",
                            placeholder="e.g., Vegetables"
                        )
                    
                    with col2:
                        category = st.selectbox(
                            "Category*",
                            options=["Meat", "Vegetables", "Grains", "Dairy", "Fruits", "Seafood", "Processed", "Other"],
                            key=f"report_category_{i}"
                        )
                    
                    with col3:
                        waste_category = st.selectbox(
                            "Waste Category*",
                            options=[cat.value for cat in WasteCategory],
                            key=f"report_waste_category_{i}"
                        )
                    
                    with col4:
                        quantity_kg = st.number_input(
                            "Quantity (kg)*",
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                            key=f"report_quantity_{i}"
                        )
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        estimated_cost = st.number_input(
                            "Estimated Cost ($)",
                            min_value=0.0,
                            step=0.01,
                            format="%.2f",
                            key=f"report_cost_{i}"
                        )
                    
                    with col2:
                        reason = st.text_input(
                            "Reason",
                            key=f"report_reason_{i}",
                            placeholder="e.g., Spoiled, Overproduction"
                        )
                    
                    if food_item and category and waste_category and quantity_kg > 0:
                        waste_entries.append({
                            'food_item': food_item,
                            'category': category,
                            'waste_category': waste_category,
                            'quantity_kg': quantity_kg,
                            'estimated_cost': estimated_cost,
                            'reason': reason
                        })
            
            elif report_type in ["CSV Upload", "Excel Upload"]:
                st.markdown(f"#### 📁 {report_type} Upload")
                
                uploaded_file = st.file_uploader(
                    f"Upload {report_type}",
                    type=["csv", "xlsx"] if report_type == "Excel Upload" else ["csv"],
                    key="report_file_upload",
                    help=f"Upload your {report_type.lower()} file"
                )
                
                if uploaded_file is not None:
                    try:
                        if report_type == "CSV Upload":
                            df = pd.read_csv(uploaded_file)
                        else:
                            df = pd.read_excel(uploaded_file)
                        
                        st.success(f"✅ {report_type} uploaded successfully!")
                        st.dataframe(df.head())
                        
                        # Validate required columns
                        required_columns = ['food_item', 'category', 'waste_category', 'quantity_kg']
                        missing_columns = [col for col in required_columns if col not in df.columns]
                        
                        if missing_columns:
                            st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                            return False
                        
                        # Convert to waste entries format
                        waste_entries = df.to_dict('records')
                        
                    except Exception as e:
                        st.error(f"❌ Error reading file: {str(e)}")
                        return False
                else:
                    waste_entries = []
            
            st.markdown("#### 📋 Report Summary")
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_waste = sum(entry.get('quantity_kg', 0) for entry in waste_entries)
                total_cost = sum(entry.get('estimated_cost', 0) for entry in waste_entries)
                
                st.metric("Total Waste (kg)", f"{total_waste:.2f}")
                st.metric("Total Cost", f"${total_cost:.2f}")
                st.metric("Number of Entries", f"{len(waste_entries)}")
            
            with col2:
                report_notes = st.text_area(
                    "Report Notes",
                    key="report_notes",
                    help="Additional notes about the daily report",
                    height=100
                )
                
                verified_by = st.text_input(
                    "Verified By",
                    key="verified_by",
                    help="Name of staff verifying the report"
                )
            
            # Submit button
            col1, col2 = st.columns(2)
            
            with col1:
                submitted = st.form_submit_button(
                    "📤 Upload Report",
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                if st.form_submit_button("🔄 Reset Form", use_container_width=True):
                    st.experimental_rerun()
            
            if submitted:
                return self._process_daily_report(
                    dining_hall, report_date, report_type,
                    waste_entries, staff_prepared_by, report_notes, verified_by
                )
        
        return False
    
    # Processing Methods
    def _process_meal_preparation(
        self, dining_hall, meal_type, preparation_date, food_items,
        preparation_method, chef_name, preparation_notes, quality_check
    ) -> bool:
        """Process meal preparation form submission."""
        try:
            # Validate data
            validation_result = validate_meal_preparation_data({
                'dining_hall': dining_hall,
                'meal_type': meal_type,
                'preparation_date': preparation_date,
                'food_items': food_items
            })
            
            if not validation_result['valid']:
                st.error("❌ Validation Error:")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                return False
            
            # Get current user ID (from session)
            user_id = st.session_state.get('user', {}).get('id', 1)
            
            # Log meal preparation
            success, message, waste_log = self.db_ops.log_meal_preparation(
                user_id=user_id,
                dining_hall=dining_hall,
                meal_type=MealType(meal_type),
                food_items=food_items,
                preparation_date=preparation_date
            )
            
            if success:
                st.success(f"✅ {message}")
                
                # Show summary
                total_quantity = sum(item['quantity_prepared'] for item in food_items)
                total_servings = sum(item['estimated_servings'] for item in food_items)
                
                st.markdown("#### 📊 Preparation Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Items", len(food_items))
                    st.metric("Total Quantity (kg)", f"{total_quantity:.2f}")
                
                with col2:
                    st.metric("Total Servings", f"{total_servings}")
                    st.metric("Avg Servings per kg", f"{total_servings/total_quantity:.1f}")
                
                return True
            else:
                st.error(f"❌ {message}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing meal preparation: {str(e)}")
            logger.error(f"Error processing meal preparation: {str(e)}")
            return False
    
    def _process_leftovers(
        self, dining_hall, meal_type, leftovers_date, service_period,
        leftover_items, storage_conditions, storage_location,
        shelf_life_hours, reuse_potential, leftovers_reason, recorded_by
    ) -> bool:
        """Process leftovers form submission."""
        try:
            # Validate data
            validation_result = validate_leftovers_data({
                'dining_hall': dining_hall,
                'meal_type': meal_type,
                'leftovers_date': leftovers_date,
                'leftover_items': leftover_items
            })
            
            if not validation_result['valid']:
                st.error("❌ Validation Error:")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                return False
            
            # Get current user ID
            user_id = st.session_state.get('user', {}).get('id', 1)
            
            success_count = 0
            total_quantity = 0
            total_cost = 0
            
            for item in leftover_items:
                success, message, waste_log = self.db_ops.log_leftovers(
                    user_id=user_id,
                    dining_hall=dining_hall,
                    meal_type=MealType(meal_type),
                    food_item=item['food_item'],
                    category=item['category'],
                    quantity_kg=item['quantity_kg'],
                    estimated_cost=item.get('estimated_cost'),
                    storage_conditions=storage_conditions,
                    leftovers_date=leftovers_date
                )
                
                if success:
                    success_count += 1
                    total_quantity += item['quantity_kg']
                    total_cost += item.get('estimated_cost', 0)
                else:
                    st.error(f"❌ Error logging {item['food_item']}: {message}")
            
            if success_count > 0:
                st.success(f"✅ Successfully logged {success_count} leftover items")
                
                # Show summary
                st.markdown("#### 📊 Leftovers Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Items Logged", success_count)
                    st.metric("Total Quantity (kg)", f"{total_quantity:.2f}")
                
                with col2:
                    st.metric("Estimated Cost", f"${total_cost:.2f}")
                    st.metric("Storage", storage_conditions)
                
                return True
            else:
                st.error("❌ No leftovers were logged")
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing leftovers: {str(e)}")
            logger.error(f"Error processing leftovers: {str(e)}")
            return False
    
    def _process_disposed_food(
        self, dining_hall, disposal_date, disposal_time, disposal_method,
        disposed_items, disposal_reason, quality_rating, staff_responsible, witness_name
    ) -> bool:
        """Process disposed food form submission."""
        try:
            # Validate data
            validation_result = validate_disposed_food_data({
                'dining_hall': dining_hall,
                'disposal_date': disposal_date,
                'disposed_items': disposed_items
            })
            
            if not validation_result['valid']:
                st.error("❌ Validation Error:")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                return False
            
            # Get current user ID
            user_id = st.session_state.get('user', {}).get('id', 1)
            
            success_count = 0
            total_quantity = 0
            total_cost = 0
            
            for item in disposed_items:
                success, message, waste_log = self.db_ops.log_disposed_food(
                    user_id=user_id,
                    dining_hall=dining_hall,
                    food_item=item['food_item'],
                    category=item['category'],
                    waste_category=item['waste_category'],
                    quantity_kg=item['quantity_kg'],
                    estimated_cost=item.get('estimated_cost'),
                    reason=disposal_reason,
                    temperature=item.get('temperature'),
                    disposal_method=disposal_method,
                    disposal_date=disposal_date
                )
                
                if success:
                    success_count += 1
                    total_quantity += item['quantity_kg']
                    total_cost += item.get('estimated_cost', 0)
                else:
                    st.error(f"❌ Error logging {item['food_item']}: {message}")
            
            if success_count > 0:
                st.success(f"✅ Successfully logged {success_count} disposed items")
                
                # Show summary
                st.markdown("#### 📊 Disposal Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Items Disposed", success_count)
                    st.metric("Total Quantity (kg)", f"{total_quantity:.2f}")
                
                with col2:
                    st.metric("Estimated Cost", f"${total_cost:.2f}")
                    st.metric("Disposal Method", disposal_method)
                
                # Environmental impact
                co2_impact = total_quantity * 5.0  # Average CO2 impact
                water_impact = total_quantity * 1000  # Average water footprint
                
                st.markdown("#### 🌍 Environmental Impact")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("CO₂ Impact (kg)", f"{co2_impact:.2f}")
                    st.metric("Water Footprint (L)", f"{water_impact:.0f}")
                
                return True
            else:
                st.error("❌ No disposed items were logged")
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing disposed food: {str(e)}")
            logger.error(f"Error processing disposed food: {str(e)}")
            return False
    
    def _process_serving_quantities(
        self, dining_hall, meal_type, service_date, expected_students,
        serving_data, service_notes, weather_conditions, special_events, staff_supervisor
    ) -> bool:
        """Process serving quantities form submission."""
        try:
            # Validate data
            validation_result = validate_serving_quantities_data({
                'dining_hall': dining_hall,
                'meal_type': meal_type,
                'service_date': service_date,
                'serving_data': serving_data
            })
            
            if not validation_result['valid']:
                st.error("❌ Validation Error:")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                return False
            
            # Get current user ID
            user_id = st.session_state.get('user', {}).get('id', 1)
            
            success, message = self.db_ops.log_serving_quantities(
                user_id=user_id,
                dining_hall=dining_hall,
                meal_type=MealType(meal_type),
                servings_data=serving_data,
                serving_date=service_date
            )
            
            if success:
                st.success(f"✅ {message}")
                
                # Calculate and show summary
                total_prepared = sum(item['servings_prepared'] for item in serving_data)
                total_served = sum(item['servings_served'] for item in serving_data)
                total_waste_servings = sum(item['waste_servings'] for item in serving_data)
                total_waste_kg = sum(item['waste_kg'] for item in serving_data)
                total_revenue = sum(item['servings_served'] * item.get('price_per_serving', 0) for item in serving_data)
                
                waste_percentage = (total_waste_servings / total_prepared * 100) if total_prepared > 0 else 0
                
                st.markdown("#### 📊 Serving Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Prepared", f"{total_prepared}")
                    st.metric("Total Served", f"{total_served}")
                    st.metric("Waste Servings", f"{total_waste_servings}")
                
                with col2:
                    st.metric("Waste (kg)", f"{total_waste_kg:.2f}")
                    st.metric("Revenue", f"${total_revenue:.2f}")
                    st.metric("Waste %", f"{waste_percentage:.1f}%")
                
                # Waste analysis
                if waste_percentage > 20:
                    st.warning("⚠️ High waste percentage detected!")
                elif waste_percentage > 10:
                    st.info("📊 Moderate waste percentage")
                else:
                    st.success("✅ Low waste percentage - Good job!")
                
                return True
            else:
                st.error(f"❌ {message}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing serving quantities: {str(e)}")
            logger.error(f"Error processing serving quantities: {str(e)}")
            return False
    
    def _process_daily_report(
        self, dining_hall, report_date, report_type,
        waste_entries, staff_prepared_by, report_notes, verified_by
    ) -> bool:
        """Process daily report upload."""
        try:
            # Validate data
            validation_result = validate_daily_report_data({
                'dining_hall': dining_hall,
                'report_date': report_date,
                'waste_entries': waste_entries
            })
            
            if not validation_result['valid']:
                st.error("❌ Validation Error:")
                for error in validation_result['errors']:
                    st.error(f"• {error}")
                return False
            
            # Get current user ID
            user_id = st.session_state.get('user', {}).get('id', 1)
            
            # Prepare report data
            report_data = {
                'dining_hall': dining_hall,
                'waste_entries': waste_entries,
                'report_type': report_type,
                'staff_prepared_by': staff_prepared_by,
                'report_notes': report_notes,
                'verified_by': verified_by
            }
            
            success, message = self.db_ops.upload_daily_report(
                user_id=user_id,
                report_data=report_data,
                report_date=report_date
            )
            
            if success:
                st.success(f"✅ {message}")
                
                # Show summary
                total_waste = sum(entry.get('quantity_kg', 0) for entry in waste_entries)
                total_cost = sum(entry.get('estimated_cost', 0) for entry in waste_entries)
                
                st.markdown("#### 📊 Report Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Waste (kg)", f"{total_waste:.2f}")
                    st.metric("Total Cost", f"${total_cost:.2f}")
                    st.metric("Entries Uploaded", f"{len(waste_entries)}")
                
                with col2:
                    st.metric("Report Type", report_type)
                    st.metric("Prepared By", staff_prepared_by)
                    st.metric("Verified By", verified_by or "Not verified")
                
                return True
            else:
                st.error(f"❌ {message}")
                return False
                
        except Exception as e:
            st.error(f"❌ Error processing daily report: {str(e)}")
            logger.error(f"Error processing daily report: {str(e)}")
            return False
    
    # Helper Methods
    def _get_dining_halls(self) -> List[str]:
        """Get list of dining halls from database."""
        try:
            dining_halls = self.db_ops.get_dining_halls_list()
            return dining_halls if dining_halls else ["Main Hall", "North Campus", "South Campus", "West Campus"]
        except Exception as e:
            logger.error(f"Error getting dining halls: {str(e)}")
            return ["Main Hall", "North Campus", "South Campus", "West Campus"]
