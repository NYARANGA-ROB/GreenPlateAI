"""
Main Streamlit application for AI forecasting system.
This module provides the complete AI forecasting interface with
demand prediction, waste forecasting, and recommendations.
"""

import streamlit as st

import pandas as pd

import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging

# Import forecasting components
from ai_forecasting.models import DemandForecastModel, WasteForecastModel, EnsembleForecastModel
from ai_forecasting.data_preprocessing import DataPreprocessor
from ai_forecasting.predictions import ForecastingEngine, DemandPredictor, WastePredictor
from ai_forecasting.charts import ForecastCharts
from ai_forecasting.recommendations import RecommendationEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Forecasting - GreenPlateAI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.forecast-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
    border-left: 4px solid #667eea;
    margin-bottom: 1rem;
}

.model-card {
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

.recommendation-card {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 1rem;
    border-left: 4px solid #28a745;
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

.priority-high {
    border-left: 4px solid #dc3545;
}

.priority-medium {
    border-left: 4px solid #ffc107;
}

.priority-low {
    border-left: 4px solid #28a745;
}
</style>
""", unsafe_allow_html=True)


class ForecastingApp:
    """Main application class for AI forecasting."""
    
    def __init__(self):
        """Initialize the application."""
        self.forecasting_engine = None
        self.charts = ForecastCharts()
        self.recommendation_engine = RecommendationEngine()
        
        # Initialize session state
        if 'models_trained' not in st.session_state:
            st.session_state.models_trained = False
        if 'selected_dining_hall' not in st.session_state:
            st.session_state.selected_dining_hall = 'Main Hall'
        if 'forecast_date' not in st.session_state:
            st.session_state.forecast_date = date.today()
        if 'model_type' not in st.session_state:
            st.session_state.model_type = 'ensemble'
    
    def run(self):
        """Run the main application."""
        # Check authentication
        if not self._check_authentication():
            return
        
        # Header
        self._show_header()
        
        # Sidebar
        self._show_sidebar()
        
        # Main content based on page
        if st.session_state.get('page', 'dashboard') == 'dashboard':
            self._show_dashboard()
        elif st.session_state.page == 'model_training':
            self._show_model_training()
        elif st.session_state.page == 'demand_forecasting':
            self._show_demand_forecasting()
        elif st.session_state.page == 'waste_forecasting':
            self._show_waste_forecasting()
        elif st.session_state.page == 'recommendations':
            self._show_recommendations()
        elif st.session_state.page == 'model_evaluation':
            self._show_model_evaluation()
        elif st.session_state.page == 'batch_forecasting':
            self._show_batch_forecasting()
    
    def _check_authentication(self) -> bool:
        """Check if user is authenticated."""
        if 'user' not in st.session_state:
            st.error("🔐 Please log in to access the AI forecasting module.")
            st.info("Please log in from the main application.")
            return False
        return True
    
    def _show_header(self):
        """Show application header."""
        st.markdown("""
        <div class="forecast-header">
            <h1>🤖 AI Forecasting System</h1>
            <p>Predict meal demand and food waste using advanced machine learning</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_sidebar(self):
        """Show sidebar navigation and controls."""
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            # Navigation menu
            pages = {
                'dashboard': '📊 Dashboard',
                'model_training': '🎯 Model Training',
                'demand_forecasting': '🍽️ Demand Forecasting',
                'waste_forecasting': '🗑️ Waste Forecasting',
                'recommendations': '💡 Recommendations',
                'model_evaluation': '📈 Model Evaluation',
                'batch_forecasting': '📅 Batch Forecasting'
            }
            
            for page_key, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                    st.session_state.page = page_key
                    st.experimental_rerun()
            
            st.markdown("---")
            st.markdown("### ⚙️ Settings")
            
            # Model type selection
            model_type = st.selectbox(
                "Model Type",
                options=["ensemble", "random_forest", "prophet"],
                index=0,
                key="model_type_select"
            )
            st.session_state.model_type = model_type
            
            # Dining hall selection
            dining_halls = ["Main Hall", "North Campus", "South Campus", "West Campus"]
            selected_hall = st.selectbox(
                "Dining Hall",
                options=dining_halls,
                index=0,
                key="dining_hall_select"
            )
            st.session_state.selected_dining_hall = selected_hall
            
            # Forecast date
            forecast_date = st.date_input(
                "Forecast Date",
                value=date.today(),
                min_value=date.today(),
                max_value=date.today() + timedelta(days=30),
                key="forecast_date_select"
            )
            st.session_state.forecast_date = forecast_date
            
            # Model status
            st.markdown("---")
            st.markdown("### 📊 Model Status")
            
            if st.session_state.models_trained:
                st.success("✅ Models trained and ready")
            else:
                st.warning("⚠️ Models need training")
                if st.button("Train Models", key="train_models_sidebar"):
                    st.session_state.page = 'model_training'
                    st.experimental_rerun()
    
    def _show_dashboard(self):
        """Show main dashboard."""
        st.markdown("## 📊 AI Forecasting Dashboard")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Initialize forecasting engine
        if self.forecasting_engine is None:
            self.forecasting_engine = ForecastingEngine(st.session_state.model_type)
        
        # Quick predictions
        st.markdown("### 🎯 Quick Predictions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🍽️ Demand Prediction")
            
            # Get demand prediction
            try:
                demand_predictor = DemandPredictor()
                demand_pred = demand_predictor.predict_meal_demand(
                    st.session_state.forecast_date,
                    st.session_state.selected_dining_hall,
                    'lunch'
                )
                
                predicted_demand = demand_pred.get('predicted_demand', 0)
                confidence = demand_pred.get('confidence', 0.8)
                
                st.metric("Predicted Demand", f"{predicted_demand:,} servings")
                st.metric("Confidence", f"{confidence:.1%}")
                
                # Demand factors
                factors = demand_pred.get('factors', {})
                if factors:
                    st.markdown("**Influencing Factors:**")
                    for key, value in factors.items():
                        st.write(f"• {key.replace('_', ' ').title()}: {value}")
                
            except Exception as e:
                st.error(f"Error getting demand prediction: {str(e)}")
        
        with col2:
            st.markdown("#### 🗑️ Waste Prediction")
            
            # Get waste prediction
            try:
                waste_predictor = WastePredictor()
                waste_pred = waste_predictor.predict_waste_by_category(
                    st.session_state.forecast_date,
                    st.session_state.selected_dining_hall,
                    'lunch'
                )
                
                predicted_waste = waste_pred.get('total_predicted_waste', 0)
                waste_percentage = waste_pred.get('waste_percentage', 0)
                
                st.metric("Predicted Waste", f"{predicted_waste:.1f} kg")
                st.metric("Waste %", f"{waste_percentage:.1f}%")
                
                # Top waste categories
                category_predictions = waste_pred.get('category_predictions', {})
                if category_predictions:
                    st.markdown("**Top Waste Categories:**")
                    sorted_categories = sorted(category_predictions.items(), key=lambda x: x[1], reverse=True)
                    for category, amount in sorted_categories[:3]:
                        st.write(f"• {category}: {amount:.1f} kg")
                
            except Exception as e:
                st.error(f"Error getting waste prediction: {str(e)}")
        
        # Recommendations preview
        st.markdown("### 💡 Today's Recommendations")
        
        try:
            recommendations = self.recommendation_engine.generate_daily_recommendations(
                st.session_state.forecast_date,
                st.session_state.selected_dining_hall
            )
            
            # Show top 3 priority actions
            priority_actions = recommendations.get('priority_actions', [])
            
            if priority_actions:
                for i, action in enumerate(priority_actions[:3], 1):
                    priority_class = {
                        9: 'priority-high',
                        8: 'priority-high',
                        7: 'priority-medium',
                        6: 'priority-medium'
                    }.get(action['priority'], 'priority-low')
                    
                    st.markdown(f"""
                    <div class="recommendation-card {priority_class}">
                        <strong>Priority {i}:</strong> {action['action']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Cost savings
            cost_savings = recommendations.get('cost_savings', {})
            if cost_savings:
                st.markdown("### 💰 Potential Cost Savings")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Waste Reduction", f"${cost_savings.get('waste_reduction', 0):.2f}")
                
                with col2:
                    st.metric("Labor", f"${cost_savings.get('labor_optimization', 0):.2f}")
                
                with col3:
                    st.metric("Inventory", f"${cost_savings.get('inventory_optimization', 0):.2f}")
                
                with col4:
                    st.metric("Total", f"${cost_savings.get('total_savings', 0):.2f}")
        
        except Exception as e:
            st.error(f"Error generating recommendations: {str(e)}")
        
        # Quick actions
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Detailed Forecast", use_container_width=True):
                st.session_state.page = 'demand_forecasting'
                st.experimental_rerun()
        
        with col2:
            if st.button("🗑️ Waste Analysis", use_container_width=True):
                st.session_state.page = 'waste_forecasting'
                st.experimental_rerun()
        
        with col3:
            if st.button("💡 All Recommendations", use_container_width=True):
                st.session_state.page = 'recommendations'
                st.experimental_rerun()
    
    def _show_model_training(self):
        """Show model training interface."""
        st.markdown("## 🎯 Model Training")
        
        st.markdown("### 📊 Training Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_type = st.selectbox(
                "Select Model Type",
                options=["ensemble", "random_forest", "prophet"],
                index=0,
                key="training_model_type"
            )
            
            data_range = st.selectbox(
                "Data Range",
                options=["Last 30 days", "Last 60 days", "Last 90 days", "Last 6 months"],
                index=0,
                key="training_data_range"
            )
        
        with col2:
            test_size = st.slider(
                "Test Size",
                min_value=0.1,
                max_value=0.4,
                value=0.2,
                step=0.05,
                key="training_test_size"
            )
            
            force_retrain = st.checkbox(
                "Force Retrain",
                value=False,
                key="training_force_retrain",
                help="Retrain models even if they already exist"
            )
        
        # Training progress
        if st.button("🚀 Start Training", type="primary", use_container_width=True):
            self._train_models(model_type, data_range, test_size, force_retrain)
        
        # Show training results
        if st.session_state.models_trained:
            self._show_training_results()
    
    def _train_models(self, model_type: str, data_range: str, test_size: float, force_retrain: bool):
        """Train the forecasting models."""
        st.markdown("### 🔄 Training Models...")
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Initialize forecasting engine
            self.forecasting_engine = ForecastingEngine(model_type)
            
            # Get data
            status_text.text("📊 Fetching historical data...")
            progress_bar.progress(20)
            
            # Calculate date range
            days_map = {
                "Last 30 days": 30,
                "Last 60 days": 60,
                "Last 90 days": 90,
                "Last 6 months": 180
            }
            days = days_map[data_range]
            
            # Train models
            status_text.text("🤖 Training demand model...")
            progress_bar.progress(40)
            
            training_results = self.forecasting_engine.train_models(test_size=test_size)
            
            status_text.text("✅ Training completed!")
            progress_bar.progress(100)
            
            # Store results
            st.session_state.training_results = training_results
            st.session_state.models_trained = True
            st.session_state.model_type = model_type
            
            # Show success message
            st.success("✅ Models trained successfully!")
            
            # Show training metrics
            self._display_training_metrics(training_results)
            
        except Exception as e:
            st.error(f"❌ Error training models: {str(e)}")
            logger.error(f"Error training models: {str(e)}")
    
    def _show_training_results(self):
        """Show training results."""
        if 'training_results' not in st.session_state:
            return
        
        training_results = st.session_state.training_results
        
        st.markdown("### 📊 Training Results")
        
        # Demand model results
        demand_metrics = training_results.get('demand', {})
        if demand_metrics and 'error' not in demand_metrics:
            st.markdown("#### 🍽️ Demand Model")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("MAE", f"{demand_metrics.get('mae', 0):.2f}")
            
            with col2:
                st.metric("RMSE", f"{demand_metrics.get('rmse', 0):.2f}")
            
            with col3:
                st.metric("R²", f"{demand_metrics.get('r2', 0):.3f}")
            
            with col4:
                st.metric("MAPE", f"{demand_metrics.get('mape', 0):.1f}%")
        
        # Waste model results
        waste_metrics = training_results.get('waste', {})
        if waste_metrics and 'error' not in waste_metrics:
            st.markdown("#### 🗑️ Waste Model")
            
            if isinstance(waste_metrics, dict) and 'mae' in waste_metrics:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("MAE", f"{waste_metrics.get('mae', 0):.2f}")
                
                with col2:
                    st.metric("RMSE", f"{waste_metrics.get('rmse', 0):.2f}")
                
                with col3:
                    st.metric("R²", f"{waste_metrics.get('r2', 0):.3f}")
                
                with col4:
                    st.metric("MAPE", f"{waste_metrics.get('mape', 0):.1f}%")
            else:
                # Category-specific models
                st.markdown("Category-specific models trained:")
                for category, metrics in waste_metrics.items():
                    if isinstance(metrics, dict) and 'mae' in metrics:
                        st.write(f"• {category}: MAE = {metrics.get('mae', 0):.2f}")
    
    def _display_training_metrics(self, training_results: Dict[str, Any]):
        """Display training metrics."""
        st.markdown("### 📈 Training Metrics")
        
        # Create performance comparison chart
        metrics = {}
        
        demand_metrics = training_results.get('demand', {})
        if demand_metrics and 'error' not in demand_metrics:
            metrics['Demand'] = demand_metrics
        
        waste_metrics = training_results.get('waste', {})
        if waste_metrics and 'error' not in waste_metrics:
            if isinstance(waste_metrics, dict) and 'mae' in waste_metrics:
                metrics['Waste'] = waste_metrics
        
        if metrics:
            fig = self.charts.create_model_performance_chart(metrics)
            st.plotly_chart(fig, use_container_width=True)
    
    def _show_demand_forecasting(self):
        """Show demand forecasting interface."""
        st.markdown("## 🍽️ Demand Forecasting")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Forecast configuration
        st.markdown("### ⚙️ Forecast Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            meal_type = st.selectbox(
                "Meal Type",
                options=["breakfast", "lunch", "dinner"],
                index=1,
                key="demand_meal_type"
            )
        
        with col2:
            horizon = st.slider(
                "Forecast Horizon (days)",
                min_value=1,
                max_value=14,
                value=7,
                key="demand_horizon"
            )
        
        with col3:
            show_confidence = st.checkbox(
                "Show Confidence Intervals",
                value=True,
                key="demand_confidence"
            )
        
        # Generate forecast
        if st.button("🔮 Generate Forecast", type="primary", use_container_width=True):
            self._generate_demand_forecast(meal_type, horizon, show_confidence)
        
        # Show forecast results
        if 'demand_forecast' in st.session_state:
            self._display_demand_forecast()
    
    def _generate_demand_forecast(self, meal_type: str, horizon: int, show_confidence: bool):
        """Generate demand forecast."""
        try:
            # Initialize forecasting engine
            if self.forecasting_engine is None:
                self.forecasting_engine = ForecastingEngine(st.session_state.model_type)
            
            # Load models if not already loaded
            if not self.forecasting_engine.is_trained:
                self._load_models()
            
            # Generate forecast
            forecast_date = st.session_state.forecast_date
            end_date = forecast_date + timedelta(days=horizon-1)
            
            batch_results = self.forecasting_engine.predict_batch(
                forecast_date, end_date, st.session_state.selected_dining_hall
            )
            
            # Filter by meal type
            filtered_predictions = [
                pred for pred in batch_results['demand_predictions']
                if pred.get('meal_type') == meal_type
            ]
            
            # Store results
            st.session_state.demand_forecast = {
                'meal_type': meal_type,
                'predictions': filtered_predictions,
                'summary': batch_results['summary'],
                'show_confidence': show_confidence
            }
            
            st.success("✅ Demand forecast generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating forecast: {str(e)}")
            logger.error(f"Error generating demand forecast: {str(e)}")
    
    def _display_demand_forecast(self):
        """Display demand forecast results."""
        forecast_data = st.session_state.demand_forecast
        
        st.markdown("### 📈 Demand Forecast Results")
        
        # Summary metrics
        summary = forecast_data.get('summary', {})
        demand_summary = summary.get('demand', {})
        
        if demand_summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Demand", f"{demand_summary.get('total', 0):.0f}")
            
            with col2:
                st.metric("Average Daily", f"{demand_summary.get('average', 0):.0f}")
            
            with col3:
                st.metric("Peak Demand", f"{demand_summary.get('max', 0):.0f}")
            
            with col4:
                st.metric("Min Demand", f"{demand_summary.get('min', 0):.0f}")
        
        # Forecast chart
        predictions = forecast_data.get('predictions', [])
        if predictions:
            # Create DataFrame for chart
            forecast_df = pd.DataFrame(predictions)
            
            # Create chart
            fig = self.charts.create_demand_forecast_chart(
                pd.DataFrame(),  # Empty historical data for now
                {
                    'dates': forecast_df['date'],
                    'predictions': forecast_df['predicted_demand']
                },
                f"Demand Forecast - {forecast_data['meal_type'].title()}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed predictions table
            st.markdown("### 📋 Detailed Predictions")
            
            display_df = forecast_df[['date', 'predicted_demand']].copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Predicted Demand']
            
            st.dataframe(display_df, use_container_width=True)
    
    def _show_waste_forecasting(self):
        """Show waste forecasting interface."""
        st.markdown("## 🗑️ Waste Forecasting")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Forecast configuration
        st.markdown("### ⚙️ Forecast Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            meal_type = st.selectbox(
                "Meal Type",
                options=["breakfast", "lunch", "dinner"],
                index=1,
                key="waste_meal_type"
            )
        
        with col2:
            horizon = st.slider(
                "Forecast Horizon (days)",
                min_value=1,
                max_value=14,
                value=7,
                key="waste_horizon"
            )
        
        with col3:
            show_categories = st.checkbox(
                "Show Category Breakdown",
                value=True,
                key="waste_categories"
            )
        
        # Generate forecast
        if st.button("🔮 Generate Forecast", type="primary", use_container_width=True):
            self._generate_waste_forecast(meal_type, horizon, show_categories)
        
        # Show forecast results
        if 'waste_forecast' in st.session_state:
            self._display_waste_forecast()
    
    def _generate_waste_forecast(self, meal_type: str, horizon: int, show_categories: bool):
        """Generate waste forecast."""
        try:
            # Initialize forecasting engine
            if self.forecasting_engine is None:
                self.forecasting_engine = ForecastingEngine(st.session_state.model_type)
            
            # Load models if not already loaded
            if not self.forecasting_engine.is_trained:
                self._load_models()
            
            # Generate forecast
            forecast_date = st.session_state.forecast_date
            end_date = forecast_date + timedelta(days=horizon-1)
            
            batch_results = self.forecasting_engine.predict_batch(
                forecast_date, end_date, st.session_state.selected_dining_hall
            )
            
            # Filter by meal type
            filtered_predictions = [
                pred for pred in batch_results['waste_predictions']
                if pred.get('meal_type') == meal_type
            ]
            
            # Store results
            st.session_state.waste_forecast = {
                'meal_type': meal_type,
                'predictions': filtered_predictions,
                'summary': batch_results['summary'],
                'show_categories': show_categories
            }
            
            st.success("✅ Waste forecast generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating forecast: {str(e)}")
            logger.error(f"Error generating waste forecast: {str(e)}")
    
    def _display_waste_forecast(self):
        """Display waste forecast results."""
        forecast_data = st.session_state.waste_forecast
        
        st.markdown("### 📈 Waste Forecast Results")
        
        # Summary metrics
        summary = forecast_data.get('summary', {})
        waste_summary = summary.get('waste', {})
        
        if waste_summary:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Waste", f"{waste_summary.get('total', 0):.1f} kg")
            
            with col2:
                st.metric("Average Daily", f"{waste_summary.get('average', 0):.1f} kg")
            
            with col3:
                st.metric("Peak Waste", f"{waste_summary.get('max', 0):.1f} kg")
            
            with col4:
                st.metric("Min Waste", f"{waste_summary.get('min', 0):.1f} kg")
        
        # Forecast chart
        predictions = forecast_data.get('predictions', [])
        if predictions:
            # Create DataFrame for chart
            forecast_df = pd.DataFrame(predictions)
            
            # Create chart
            fig = self.charts.create_waste_forecast_chart(
                pd.DataFrame(),  # Empty historical data for now
                {
                    'dates': forecast_df['date'],
                    'predictions': forecast_df['total_predicted_waste']
                },
                f"Waste Forecast - {forecast_data['meal_type'].title()}"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Category breakdown
            if forecast_data['show_categories']:
                st.markdown("### 📊 Category Breakdown")
                
                # Aggregate category predictions
                category_totals = {}
                for pred in predictions:
                    category_preds = pred.get('category_predictions', {})
                    for category, amount in category_preds.items():
                        if isinstance(amount, list) and len(amount) > 0:
                            amount = amount[0]
                        elif isinstance(amount, np.ndarray) and len(amount) > 0:
                            amount = float(amount[0])
                        
                        if category in category_totals:
                            category_totals[category] += amount
                        else:
                            category_totals[category] = amount
                
                if category_totals:
                    fig = self.charts.create_category_waste_chart(category_totals)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Detailed predictions table
            st.markdown("### 📋 Detailed Predictions")
            
            display_df = forecast_df[['date', 'total_predicted_waste']].copy()
            display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Predicted Waste (kg)']
            
            st.dataframe(display_df, use_container_width=True)
    
    def _show_recommendations(self):
        """Show recommendations interface."""
        st.markdown("## 💡 AI Recommendations")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Generate recommendations
        if st.button("🎯 Generate Recommendations", type="primary", use_container_width=True):
            self._generate_recommendations()
        
        # Show recommendations
        if 'recommendations' in st.session_state:
            self._display_recommendations()
    
    def _generate_recommendations(self):
        """Generate AI recommendations."""
        try:
            recommendations = self.recommendation_engine.generate_daily_recommendations(
                st.session_state.forecast_date,
                st.session_state.selected_dining_hall
            )
            
            st.session_state.recommendations = recommendations
            st.success("✅ Recommendations generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating recommendations: {str(e)}")
            logger.error(f"Error generating recommendations: {str(e)}")
    
    def _display_recommendations(self):
        """Display recommendations results."""
        recommendations = st.session_state.recommendations
        
        st.markdown("### 🎯 AI Recommendations for Today")
        
        # Cost savings
        cost_savings = recommendations.get('cost_savings', {})
        if cost_savings:
            st.markdown("### 💰 Potential Cost Savings")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Waste Reduction", f"${cost_savings.get('waste_reduction', 0):.2f}")
            
            with col2:
                st.metric("Labor", f"${cost_savings.get('labor_optimization', 0):.2f}")
            
            with col3:
                st.metric("Inventory", f"${cost_savings.get('inventory_optimization', 0):.2f}")
            
            with col4:
                st.metric("Total", f"${cost_savings.get('total_savings', 0):.2f}")
        
        # Priority actions
        priority_actions = recommendations.get('priority_actions', [])
        if priority_actions:
            st.markdown("### 🚀 Priority Actions")
            
            for i, action in enumerate(priority_actions[:10], 1):
                priority_class = {
                    9: 'priority-high',
                    8: 'priority-high',
                    7: 'priority-medium',
                    6: 'priority-medium'
                }.get(action['priority'], 'priority-low')
                
                st.markdown(f"""
                <div class="recommendation-card {priority_class}">
                    <strong>Priority {i}:</strong> {action['action']}
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed recommendations
        st.markdown("### 📋 Detailed Recommendations")
        
        # Demand recommendations
        demand_recs = recommendations.get('demand_recommendations', [])
        if demand_recs:
            st.markdown("#### 🍽️ Demand Recommendations")
            for rec in demand_recs:
                st.info(f"• {rec}")
        
        # Waste recommendations
        waste_recs = recommendations.get('waste_recommendations', [])
        if waste_recs:
            st.markdown("#### 🗑️ Waste Recommendations")
            for rec in waste_recs:
                st.warning(f"• {rec}")
        
        # Operational recommendations
        operational_recs = recommendations.get('operational_recommendations', [])
        if operational_recs:
            st.markdown("#### ⚙️ Operational Recommendations")
            for rec in operational_recs:
                st.info(f"• {rec}")
    
    def _show_model_evaluation(self):
        """Show model evaluation interface."""
        st.markdown("## 📈 Model Evaluation")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Evaluate models
        if st.button("🔍 Evaluate Models", type="primary", use_container_width=True):
            self._evaluate_models()
        
        # Show evaluation results
        if 'evaluation_results' in st.session_state:
            self._display_evaluation_results()
    
    def _evaluate_models(self):
        """Evaluate model performance."""
        try:
            # Initialize forecasting engine
            if self.forecasting_engine is None:
                self.forecasting_engine = ForecastingEngine(st.session_state.model_type)
            
            # Load models if not already loaded
            if not self.forecasting_engine.is_trained:
                self._load_models()
            
            # Get test data
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            preprocessor = DataPreprocessor()
            test_data = preprocessor.get_historical_data(start_date, end_date)
            
            if test_data.empty:
                st.warning("⚠️ No test data available for evaluation")
                return
            
            # Evaluate models
            evaluation_results = self.forecasting_engine.evaluate_models(test_data)
            
            st.session_state.evaluation_results = evaluation_results
            st.success("✅ Model evaluation completed!")
            
        except Exception as e:
            st.error(f"❌ Error evaluating models: {str(e)}")
            logger.error(f"Error evaluating models: {str(e)}")
    
    def _display_evaluation_results(self):
        """Display evaluation results."""
        evaluation_results = st.session_state.evaluation_results
        
        st.markdown("### 📊 Model Performance Evaluation")
        
        # Create performance chart
        metrics = {}
        
        demand_eval = evaluation_results.get('demand', {})
        if demand_eval and 'error' not in demand_eval:
            metrics['Demand Model'] = demand_eval
        
        waste_eval = evaluation_results.get('waste', {})
        if waste_eval and 'error' not in waste_eval:
            metrics['Waste Model'] = waste_eval
        
        if metrics:
            fig = self.charts.create_model_performance_chart(metrics)
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed metrics
        st.markdown("### 📋 Detailed Metrics")
        
        # Demand model metrics
        if demand_eval and 'error' not in demand_eval:
            st.markdown("#### 🍽️ Demand Model")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("MAE", f"{demand_eval.get('mae', 0):.2f}")
            
            with col2:
                st.metric("RMSE", f"{demand_eval.get('rmse', 0):.2f}")
            
            with col3:
                st.metric("R²", f"{demand_eval.get('r2', 0):.3f}")
            
            with col4:
                st.metric("MAPE", f"{demand_eval.get('mape', 0):.1f}%")
        
        # Waste model metrics
        if waste_eval and 'error' not in waste_eval:
            st.markdown("#### 🗑️ Waste Model")
            
            if isinstance(waste_eval, dict) and 'mae' in waste_eval:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("MAE", f"{waste_eval.get('mae', 0):.2f}")
                
                with col2:
                    st.metric("RMSE", f"{waste_eval.get('rmse', 0):.2f}")
                
                with col3:
                    st.metric("R²", f"{waste_eval.get('r2', 0):.3f}")
                
                with col4:
                    st.metric("MAPE", f"{waste_eval.get('mape', 0):.1f}%")
    
    def _show_batch_forecasting(self):
        """Show batch forecasting interface."""
        st.markdown("## 📅 Batch Forecasting")
        
        if not st.session_state.models_trained:
            st.warning("⚠️ Models need to be trained first. Go to Model Training to get started.")
            return
        
        # Batch configuration
        st.markdown("### ⚙️ Batch Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.today(),
                key="batch_start_date"
            )
            
            end_date = st.date_input(
                "End Date",
                value=date.today() + timedelta(days=7),
                key="batch_end_date"
            )
        
        with col2:
            include_meals = st.multiselect(
                "Include Meals",
                options=["breakfast", "lunch", "dinner"],
                default=["breakfast", "lunch", "dinner"],
                key="batch_meals"
            )
            
            show_charts = st.checkbox(
                "Include Charts",
                value=True,
                key="batch_charts"
            )
        
        # Generate batch forecast
        if st.button("📊 Generate Batch Forecast", type="primary", use_container_width=True):
            self._generate_batch_forecast(start_date, end_date, include_meals, show_charts)
        
        # Show batch results
        if 'batch_forecast' in st.session_state:
            self._display_batch_forecast()
    
    def _generate_batch_forecast(self, start_date: date, end_date: date, 
                                include_meals: List[str], show_charts: bool):
        """Generate batch forecast."""
        try:
            # Initialize forecasting engine
            if self.forecasting_engine is None:
                self.forecasting_engine = ForecastingEngine(st.session_state.model_type)
            
            # Load models if not already loaded
            if not self.forecasting_engine.is_trained:
                self._load_models()
            
            # Generate batch forecast
            batch_results = self.forecasting_engine.predict_batch(
                start_date, end_date, st.session_state.selected_dining_hall
            )
            
            # Filter by meal types
            filtered_demand = [
                pred for pred in batch_results['demand_predictions']
                if pred.get('meal_type') in include_meals
            ]
            
            filtered_waste = [
                pred for pred in batch_results['waste_predictions']
                if pred.get('meal_type') in include_meals
            ]
            
            # Store results
            st.session_state.batch_forecast = {
                'period': batch_results['period'],
                'demand_predictions': filtered_demand,
                'waste_predictions': filtered_waste,
                'summary': batch_results['summary'],
                'show_charts': show_charts
            }
            
            st.success("✅ Batch forecast generated successfully!")
            
        except Exception as e:
            st.error(f"❌ Error generating batch forecast: {str(e)}")
            logger.error(f"Error generating batch forecast: {str(e)}")
    
    def _display_batch_forecast(self):
        """Display batch forecast results."""
        batch_results = st.session_state.batch_forecast
        
        st.markdown("### 📊 Batch Forecast Results")
        
        # Period information
        period = batch_results.get('period', {})
        st.markdown(f"**Forecast Period:** {period.get('start_date', 'N/A')} to {period.get('end_date', 'N/A')} ({period.get('days', 0)} days)")
        
        # Summary metrics
        summary = batch_results.get('summary', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            demand_summary = summary.get('demand', {})
            if demand_summary:
                st.markdown("#### 🍽️ Demand Summary")
                st.metric("Total Demand", f"{demand_summary.get('total', 0):.0f}")
                st.metric("Daily Average", f"{demand_summary.get('average', 0):.0f}")
                st.metric("Peak Day", demand_summary.get('peak_day', 'N/A'))
        
        with col2:
            waste_summary = summary.get('waste', {})
            if waste_summary:
                st.markdown("#### 🗑️ Waste Summary")
                st.metric("Total Waste", f"{waste_summary.get('total', 0):.1f} kg")
                st.metric("Daily Average", f"{waste_summary.get('average', 0):.1f} kg")
                st.metric("Peak Day", waste_summary.get('peak_day', 'N/A'))
        
        # Charts
        if batch_results['show_charts']:
            st.markdown("### 📈 Forecast Charts")
            
            # Demand chart
            demand_predictions = batch_results.get('demand_predictions', [])
            if demand_predictions:
                demand_df = pd.DataFrame(demand_predictions)
                
                fig = self.charts.create_weekly_forecast_chart(
                    batch_results,
                    "Weekly Demand Forecast"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Waste chart
            waste_predictions = batch_results.get('waste_predictions', [])
            if waste_predictions:
                waste_df = pd.DataFrame(waste_predictions)
                
                fig = self.charts.create_waste_forecast_chart(
                    pd.DataFrame(),
                    {
                        'dates': waste_df['date'],
                        'predictions': waste_df['total_predicted_waste']
                    },
                    "Weekly Waste Forecast"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Detailed tables
        st.markdown("### 📋 Detailed Predictions")
        
        tab1, tab2 = st.tabs(["Demand Predictions", "Waste Predictions"])
        
        with tab1:
            demand_predictions = batch_results.get('demand_predictions', [])
            if demand_predictions:
                demand_df = pd.DataFrame(demand_predictions)
                demand_df['date'] = pd.to_datetime(demand_df['date']).dt.strftime('%Y-%m-%d')
                display_df = demand_df[['date', 'meal_type', 'predicted_demand']].copy()
                display_df.columns = ['Date', 'Meal Type', 'Predicted Demand']
                st.dataframe(display_df, use_container_width=True)
        
        with tab2:
            waste_predictions = batch_results.get('waste_predictions', [])
            if waste_predictions:
                waste_df = pd.DataFrame(waste_predictions)
                waste_df['date'] = pd.to_datetime(waste_df['date']).dt.strftime('%Y-%m-%d')
                display_df = waste_df[['date', 'meal_type', 'total_predicted_waste']].copy()
                display_df.columns = ['Date', 'Meal Type', 'Predicted Waste (kg)']
                st.dataframe(display_df, use_container_width=True)
    
    def _load_models(self):
        """Load pre-trained models."""
        try:
            # Try to load models from disk
            model_dir = Path("models/forecasting")
            
            demand_model_path = None
            waste_model_path = None
            
            # Find latest model files
            for file_path in model_dir.glob("*demand*.pkl"):
                demand_model_path = str(file_path)
                break
            
            for file_path in model_dir.glob("*waste*.pkl"):
                waste_model_path = str(file_path)
                break
            
            if demand_model_path and waste_model_path:
                success = self.forecasting_engine.load_models(demand_model_path, waste_model_path)
                if success:
                    st.session_state.models_trained = True
                    return
            
            # If no models found, train new ones
            st.warning("No pre-trained models found. Training new models...")
            training_results = self.forecasting_engine.train_models()
            st.session_state.training_results = training_results
            st.session_state.models_trained = True
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            logger.error(f"Error loading models: {str(e)}")


def main():
    """Main function to run the AI forecasting app."""
    try:
        app = ForecastingApp()
        app.run()
    except Exception as e:
        logger.error(f"Error running AI forecasting app: {str(e)}")
        st.error(f"❌ An error occurred: {str(e)}")
        st.info("Please refresh the page and try again.")


if __name__ == "__main__":
    main()
