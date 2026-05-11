"""
Prediction functions for AI forecasting system.

This module provides comprehensive prediction functions for
meal demand and food waste forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from pathlib import Path

from .models import DemandForecastModel, WasteForecastModel, EnsembleForecastModel
from .data_preprocessing import DataPreprocessor

logger = logging.getLogger(__name__)


class ForecastingEngine:
    """Main forecasting engine for demand and waste predictions."""
    
    def __init__(self, model_type: str = "ensemble"):
        """Initialize the forecasting engine."""
        self.model_type = model_type.lower()
        self.preprocessor = DataPreprocessor()
        self.demand_model = None
        self.waste_model = None
        self.is_trained = False
        self.model_cache = {}
        
        # Model paths
        self.model_dir = Path("models/forecasting")
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    def train_models(self, data: pd.DataFrame = None, force_retrain: bool = False) -> Dict[str, Any]:
        """Train demand and waste forecasting models."""
        logger.info(f"Training {self.model_type} forecasting models")
        
        # Get data if not provided
        if data is None:
            data = self.preprocessor.get_historical_data()
        
        if data.empty:
            raise ValueError("No data available for training")
        
        # Preprocess data
        processed_data = self.preprocessor.clean_data(
            self.preprocessor.add_external_features(data)
        )
        
        training_results = {}
        
        # Train demand model
        try:
            if self.model_type == "ensemble":
                self.demand_model = EnsembleForecastModel(["random_forest"])
            else:
                self.demand_model = DemandForecastModel(self.model_type)
            
            demand_metrics = self.demand_model.train(processed_data, 'demand')
            training_results['demand'] = demand_metrics
            
            # Save model
            model_path = self.demand_model.save_model()
            training_results['demand']['model_path'] = model_path
            
        except Exception as e:
            logger.error(f"Error training demand model: {str(e)}")
            training_results['demand'] = {'error': str(e)}
        
        # Train waste model
        try:
            if self.model_type == "ensemble":
                self.waste_model = EnsembleForecastModel(["random_forest"])
            else:
                self.waste_model = WasteForecastModel(self.model_type)
            
            # Train category-specific waste models
            if isinstance(self.waste_model, WasteForecastModel):
                waste_metrics = self.waste_model.train_category_models(processed_data, 'quantity')
            else:
                waste_metrics = self.waste_model.train(processed_data, 'quantity')
            
            training_results['waste'] = waste_metrics
            
            # Save model
            model_path = self.waste_model.save_model()
            training_results['waste']['model_path'] = model_path
            
        except Exception as e:
            logger.error(f"Error training waste model: {str(e)}")
            training_results['waste'] = {'error': str(e)}
        
        self.is_trained = True
        
        logger.info("Model training completed")
        
        return training_results
    
    def predict_demand(self, forecast_date: date, dining_hall: str = None, 
                      meal_type: str = None, horizon: int = 1) -> Dict[str, Any]:
        """Predict meal demand for specified date and conditions."""
        if not self.is_trained:
            raise ValueError("Models must be trained before making predictions")
        
        logger.info(f"Predicting demand for {forecast_date}")
        
        # Prepare prediction data
        prediction_data = self._prepare_prediction_data(forecast_date, dining_hall, meal_type)
        
        # Make predictions
        demand_predictions = self.demand_model.predict(prediction_data, horizon)
        
        # Format results
        results = {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'meal_type': meal_type,
            'predictions': demand_predictions,
            'confidence_intervals': None,
            'model_type': self.demand_model.model_type
        }
        
        # Add confidence intervals if available
        if 'lower_bound' in demand_predictions and 'upper_bound' in demand_predictions:
            results['confidence_intervals'] = {
                'lower': demand_predictions['lower_bound'],
                'upper': demand_predictions['upper_bound']
            }
        
        return results
    
    def predict_waste(self, forecast_date: date, dining_hall: str = None, 
                     meal_type: str = None, category: str = None, 
                     horizon: int = 1) -> Dict[str, Any]:
        """Predict food waste for specified date and conditions."""
        if not self.is_trained:
            raise ValueError("Models must be trained before making predictions")
        
        logger.info(f"Predicting waste for {forecast_date}")
        
        # Prepare prediction data
        prediction_data = self._prepare_prediction_data(forecast_date, dining_hall, meal_type)
        
        # Make predictions
        if isinstance(self.waste_model, WasteForecastModel) and category:
            # Category-specific prediction
            waste_predictions = self.waste_model.predict_category_waste(
                prediction_data, category, horizon
            )
        else:
            # Total waste prediction
            waste_predictions = self.waste_model.predict(prediction_data, horizon)
        
        # Format results
        results = {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'meal_type': meal_type,
            'category': category,
            'predictions': waste_predictions,
            'confidence_intervals': None,
            'model_type': self.waste_model.model_type
        }
        
        # Add confidence intervals if available
        if 'lower_bound' in waste_predictions and 'upper_bound' in waste_predictions:
            results['confidence_intervals'] = {
                'lower': waste_predictions['lower_bound'],
                'upper': waste_predictions['upper_bound']
            }
        
        return results
    
    def predict_batch(self, start_date: date, end_date: date, 
                     dining_hall: str = None, meal_type: str = None) -> Dict[str, Any]:
        """Predict demand and waste for a date range."""
        logger.info(f"Batch predicting from {start_date} to {end_date}")
        
        # Calculate number of days
        days = (end_date - start_date).days + 1
        
        # Prepare results
        batch_results = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'demand_predictions': [],
            'waste_predictions': [],
            'summary': {}
        }
        
        # Predict for each day
        current_date = start_date
        while current_date <= end_date:
            # Demand prediction
            try:
                demand_pred = self.predict_demand(current_date, dining_hall, meal_type)
                batch_results['demand_predictions'].append(demand_pred)
            except Exception as e:
                logger.error(f"Error predicting demand for {current_date}: {str(e)}")
            
            # Waste prediction
            try:
                waste_pred = self.predict_waste(current_date, dining_hall, meal_type)
                batch_results['waste_predictions'].append(waste_pred)
            except Exception as e:
                logger.error(f"Error predicting waste for {current_date}: {str(e)}")
            
            current_date += timedelta(days=1)
        
        # Calculate summary statistics
        batch_results['summary'] = self._calculate_batch_summary(batch_results)
        
        return batch_results
    
    def _prepare_prediction_data(self, forecast_date: date, dining_hall: str = None, 
                               meal_type: str = None) -> pd.DataFrame:
        """Prepare data for prediction."""
        # Create a single row with the prediction features
        data = {
            'date': [forecast_date],
            'dining_hall': [dining_hall or 'Main Hall'],
            'meal_type': [meal_type or 'lunch']
        }
        
        df = pd.DataFrame(data)
        
        # Add external features
        df = self.preprocessor.add_external_features(df)
        
        return df
    
    def _calculate_batch_summary(self, batch_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for batch predictions."""
        summary = {}
        
        # Demand summary
        if batch_results['demand_predictions']:
            demand_values = []
            for pred in batch_results['demand_predictions']:
                if 'predictions' in pred and 'predictions' in pred['predictions']:
                    demand_values.extend(pred['predictions']['predictions'])
            
            if demand_values:
                summary['demand'] = {
                    'total': sum(demand_values),
                    'average': np.mean(demand_values),
                    'min': min(demand_values),
                    'max': max(demand_values),
                    'std': np.std(demand_values)
                }
        
        # Waste summary
        if batch_results['waste_predictions']:
            waste_values = []
            for pred in batch_results['waste_predictions']:
                if 'predictions' in pred and 'predictions' in pred['predictions']:
                    waste_values.extend(pred['predictions']['predictions'])
            
            if waste_values:
                summary['waste'] = {
                    'total': sum(waste_values),
                    'average': np.mean(waste_values),
                    'min': min(waste_values),
                    'max': max(waste_values),
                    'std': np.std(waste_values)
                }
        
        return summary
    
    def load_models(self, demand_model_path: str = None, waste_model_path: str = None) -> bool:
        """Load pre-trained models."""
        try:
            # Load demand model
            if demand_model_path:
                self.demand_model = DemandForecastModel()
                if self.demand_model.load_model(demand_model_path):
                    logger.info("Demand model loaded successfully")
                else:
                    return False
            
            # Load waste model
            if waste_model_path:
                self.waste_model = WasteForecastModel()
                if self.waste_model.load_model(waste_model_path):
                    logger.info("Waste model loaded successfully")
                else:
                    return False
            
            self.is_trained = True
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            return False
    
    def evaluate_models(self, test_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Evaluate model performance."""
        if not self.is_trained:
            raise ValueError("Models must be trained before evaluation")
        
        logger.info("Evaluating model performance")
        
        # Get test data if not provided
        if test_data is None:
            # Get last 30 days for evaluation
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            test_data = self.preprocessor.get_historical_data(start_date, end_date)
        
        if test_data.empty:
            raise ValueError("No test data available")
        
        # Preprocess test data
        processed_data = self.preprocessor.clean_data(
            self.preprocessor.add_external_features(test_data)
        )
        
        evaluation_results = {}
        
        # Evaluate demand model
        try:
            demand_eval = self.demand_model.evaluate(processed_data, 'demand')
            evaluation_results['demand'] = demand_eval
        except Exception as e:
            logger.error(f"Error evaluating demand model: {str(e)}")
            evaluation_results['demand'] = {'error': str(e)}
        
        # Evaluate waste model
        try:
            waste_eval = self.waste_model.evaluate(processed_data, 'quantity')
            evaluation_results['waste'] = waste_eval
        except Exception as e:
            logger.error(f"Error evaluating waste model: {str(e)}")
            evaluation_results['waste'] = {'error': str(e)}
        
        return evaluation_results


class DemandPredictor:
    """Specialized class for demand prediction."""
    
    def __init__(self, model: DemandForecastModel = None):
        """Initialize demand predictor."""
        self.model = model
        self.preprocessor = DataPreprocessor()
    
    def predict_meal_demand(self, forecast_date: date, dining_hall: str, 
                           meal_type: str, menu_items: List[str] = None) -> Dict[str, Any]:
        """Predict demand for specific meal."""
        logger.info(f"Predicting meal demand for {forecast_date} at {dining_hall}")
        
        # Prepare base prediction data
        prediction_data = self._prepare_meal_prediction_data(
            forecast_date, dining_hall, meal_type, menu_items
        )
        
        # Make prediction
        if self.model:
            predictions = self.model.predict(prediction_data)
        else:
            # Fallback to simple prediction
            predictions = self._simple_demand_prediction(forecast_date, dining_hall, meal_type)
        
        # Format results
        result = {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'meal_type': meal_type,
            'predicted_demand': predictions.get('predictions', [0])[0],
            'confidence': self._calculate_confidence(predictions),
            'factors': self._get_prediction_factors(forecast_date, dining_hall, meal_type)
        }
        
        # Add menu-specific predictions if menu items provided
        if menu_items:
            result['menu_predictions'] = self._predict_menu_demand(
                result['predicted_demand'], menu_items
            )
        
        return result
    
    def predict_weekly_demand(self, start_date: date, dining_hall: str) -> Dict[str, Any]:
        """Predict demand for a week."""
        logger.info(f"Predicting weekly demand starting {start_date}")
        
        weekly_predictions = []
        
        # Predict for each day of the week
        for day_offset in range(7):
            current_date = start_date + timedelta(days=day_offset)
            
            # Predict for each meal type
            for meal_type in ['breakfast', 'lunch', 'dinner']:
                try:
                    prediction = self.predict_meal_demand(current_date, dining_hall, meal_type)
                    weekly_predictions.append(prediction)
                except Exception as e:
                    logger.error(f"Error predicting for {current_date} {meal_type}: {str(e)}")
        
        # Calculate weekly summary
        total_demand = sum(pred['predicted_demand'] for pred in weekly_predictions)
        
        return {
            'week_start': start_date.isoformat(),
            'dining_hall': dining_hall,
            'daily_predictions': weekly_predictions,
            'total_weekly_demand': total_demand,
            'average_daily_demand': total_demand / 7,
            'peak_day': max(weekly_predictions, key=lambda x: x['predicted_demand'])['date']
        }
    
    def _prepare_meal_prediction_data(self, forecast_date: date, dining_hall: str, 
                                     meal_type: str, menu_items: List[str] = None) -> pd.DataFrame:
        """Prepare data for meal prediction."""
        data = {
            'date': [forecast_date],
            'dining_hall': [dining_hall],
            'meal_type': [meal_type],
            'menu_complexity': [len(menu_items) if menu_items else 3],
            'has_special_dish': [1 if menu_items and len(menu_items) > 5 else 0]
        }
        
        df = pd.DataFrame(data)
        df = self.preprocessor.add_external_features(df)
        
        return df
    
    def _simple_demand_prediction(self, forecast_date: date, dining_hall: str, 
                                 meal_type: str) -> Dict[str, Any]:
        """Simple fallback prediction using historical patterns."""
        # Get historical data for similar conditions
        historical_data = self.preprocessor.get_historical_data(
            forecast_date - timedelta(days=30), forecast_date - timedelta(days=1)
        )
        
        if historical_data.empty:
            # Default prediction
            default_demand = {
                'breakfast': 200,
                'lunch': 500,
                'dinner': 400
            }
            return {'predictions': [default_demand.get(meal_type, 300)]}
        
        # Filter for similar conditions
        similar_data = historical_data[
            (historical_data['dining_hall'] == dining_hall) &
            (historical_data['meal_type'] == meal_type)
        ]
        
        if similar_data.empty:
            # Use all data for this meal type
            similar_data = historical_data[historical_data['meal_type'] == meal_type]
        
        if similar_data.empty:
            # Default prediction
            default_demand = {
                'breakfast': 200,
                'lunch': 500,
                'dinner': 400
            }
            return {'predictions': [default_demand.get(meal_type, 300)]}
        
        # Calculate average demand
        avg_demand = similar_data['demand'].mean()
        
        # Adjust for day of week
        day_of_week = forecast_date.weekday()
        weekday_multiplier = {
            0: 1.1,  # Monday
            1: 1.0,  # Tuesday
            2: 1.0,  # Wednesday
            3: 1.0,  # Thursday
            4: 1.2,  # Friday
            5: 0.8,  # Saturday
            6: 0.7   # Sunday
        }
        
        adjusted_demand = avg_demand * weekday_multiplier.get(day_of_week, 1.0)
        
        return {'predictions': [int(adjusted_demand)]}
    
    def _calculate_confidence(self, predictions: Dict[str, Any]) -> float:
        """Calculate prediction confidence."""
        if 'lower_bound' in predictions and 'upper_bound' in predictions:
            pred = predictions['predictions'][0]
            lower = predictions['lower_bound'][0]
            upper = predictions['upper_bound'][0]
            
            # Confidence based on interval width
            interval_width = upper - lower
            confidence = max(0, min(1, 1 - (interval_width / (pred + 1))))
            
            return confidence
        else:
            # Default confidence
            return 0.8
    
    def _get_prediction_factors(self, forecast_date: date, dining_hall: str, 
                               meal_type: str) -> Dict[str, Any]:
        """Get factors affecting the prediction."""
        factors = {}
        
        # Day of week factor
        day_of_week = forecast_date.weekday()
        factors['day_of_week'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day_of_week]
        
        # Season factor
        month = forecast_date.month
        if month in [12, 1, 2]:
            factors['season'] = 'Winter'
        elif month in [3, 4, 5]:
            factors['season'] = 'Spring'
        elif month in [6, 7, 8]:
            factors['season'] = 'Summer'
        else:
            factors['season'] = 'Fall'
        
        # Academic period
        factors['academic_period'] = self._get_academic_period(forecast_date)
        
        # Weather factor (simplified)
        factors['weather_factor'] = 'Normal'
        
        return factors
    
    def _get_academic_period(self, date_obj: date) -> str:
        """Get academic period for date."""
        month = date_obj.month
        day = date_obj.day
        
        if (month == 12 and day >= 20) or (month == 1 and day <= 15):
            return 'Winter Break'
        elif month in [1, 2, 3, 4, 5]:
            return 'Spring Semester'
        elif month in [6, 7, 8]:
            return 'Summer Break'
        else:
            return 'Fall Semester'
    
    def _predict_menu_demand(self, total_demand: int, menu_items: List[str]) -> Dict[str, float]:
        """Predict demand for each menu item."""
        if not menu_items:
            return {}
        
        # Simple proportional distribution
        base_demand_per_item = total_demand / len(menu_items)
        
        # Adjust based on item popularity (simplified)
        popularity_adjustments = {
            'chicken': 1.2,
            'beef': 1.1,
            'fish': 0.9,
            'vegetarian': 0.8,
            'pasta': 1.3,
            'rice': 1.0,
            'salad': 0.7,
            'soup': 0.8
        }
        
        menu_predictions = {}
        remaining_demand = total_demand
        
        for i, item in enumerate(menu_items):
            # Get popularity adjustment
            adjustment = 1.0
            for keyword, adj in popularity_adjustments.items():
                if keyword.lower() in item.lower():
                    adjustment = adj
                    break
            
            # Calculate demand for this item
            if i == len(menu_items) - 1:
                # Last item gets remaining demand
                item_demand = remaining_demand
            else:
                item_demand = base_demand_per_item * adjustment
                remaining_demand -= item_demand
            
            menu_predictions[item] = max(1, int(item_demand))
        
        return menu_predictions


class WastePredictor:
    """Specialized class for waste prediction."""
    
    def __init__(self, model: WasteForecastModel = None):
        """Initialize waste predictor."""
        self.model = model
        self.preprocessor = DataPreprocessor()
    
    def predict_waste_by_category(self, forecast_date: date, dining_hall: str, 
                                 meal_type: str) -> Dict[str, Any]:
        """Predict waste by category."""
        logger.info(f"Predicting waste by category for {forecast_date}")
        
        # Prepare prediction data
        prediction_data = self._prepare_waste_prediction_data(forecast_date, dining_hall, meal_type)
        
        # Make predictions
        if self.model and isinstance(self.model, WasteForecastModel):
            total_waste = self.model.predict_total_waste(prediction_data)
            category_predictions = total_waste.get('category_predictions', {})
        else:
            # Fallback prediction
            total_waste = self._simple_waste_prediction(forecast_date, dining_hall, meal_type)
            category_predictions = self._simple_category_prediction(total_waste)
        
        return {
            'date': forecast_date.isoformat(),
            'dining_hall': dining_hall,
            'meal_type': meal_type,
            'total_predicted_waste': total_waste.get('total_predictions', [0])[0] if isinstance(total_waste.get('total_predictions'), np.ndarray) else total_waste.get('total_predictions', 0),
            'category_predictions': category_predictions,
            'waste_percentage': self._calculate_waste_percentage(total_waste),
            'recommendations': self._generate_waste_recommendations(category_predictions)
        }
    
    def _prepare_waste_prediction_data(self, forecast_date: date, dining_hall: str, 
                                     meal_type: str) -> pd.DataFrame:
        """Prepare data for waste prediction."""
        data = {
            'date': [forecast_date],
            'dining_hall': [dining_hall],
            'meal_type': [meal_type]
        }
        
        df = pd.DataFrame(data)
        df = self.preprocessor.add_external_features(df)
        
        return df
    
    def _simple_waste_prediction(self, forecast_date: date, dining_hall: str, 
                               meal_type: str) -> Dict[str, Any]:
        """Simple fallback waste prediction."""
        # Base waste rates by meal type
        base_waste_rates = {
            'breakfast': 0.08,  # 8% waste
            'lunch': 0.12,      # 12% waste
            'dinner': 0.10     # 10% waste
        }
        
        # Get predicted demand (simplified)
        demand_predictor = DemandPredictor()
        demand_pred = demand_predictor.predict_meal_demand(forecast_date, dining_hall, meal_type)
        predicted_demand = demand_pred['predicted_demand']
        
        # Calculate waste
        waste_rate = base_waste_rates.get(meal_type, 0.10)
        predicted_waste = predicted_demand * waste_rate
        
        return {'total_predictions': [int(predicted_waste)]}
    
    def _simple_category_prediction(self, total_waste: Union[Dict, float, int]) -> Dict[str, float]:
        """Simple category waste prediction."""
        total = total_waste.get('total_predictions', [0])[0] if isinstance(total_waste, dict) else total_waste
        if isinstance(total, np.ndarray):
            total = total[0]
        
        # Typical waste distribution
        category_distribution = {
            'Vegetables': 0.35,
            'Grains': 0.25,
            'Meat': 0.20,
            'Dairy': 0.10,
            'Fruits': 0.05,
            'Other': 0.05
        }
        
        category_predictions = {}
        for category, percentage in category_distribution.items():
            category_predictions[category] = total * percentage
        
        return category_predictions
    
    def _calculate_waste_percentage(self, waste_predictions: Dict[str, Any]) -> float:
        """Calculate waste percentage."""
        total_waste = waste_predictions.get('total_predictions', [0])[0] if isinstance(waste_predictions.get('total_predictions'), np.ndarray) else waste_predictions.get('total_predictions', 0)
        
        # Simplified - assume 10% average waste rate
        estimated_demand = total_waste / 0.1 if total_waste > 0 else 0
        waste_percentage = (total_waste / estimated_demand * 100) if estimated_demand > 0 else 0
        
        return min(waste_percentage, 50)  # Cap at 50%
    
    def _generate_waste_recommendations(self, category_predictions: Dict[str, float]) -> List[str]:
        """Generate waste reduction recommendations."""
        recommendations = []
        
        # Find highest waste categories
        if category_predictions:
            sorted_categories = sorted(category_predictions.items(), key=lambda x: x[1], reverse=True)
            
            for category, waste_amount in sorted_categories[:3]:
                if waste_amount > 5:  # Only recommend for significant waste
                    reduction_percentage = min(50, int(waste_amount / 2))
                    recommendations.append(
                        f"Reduce {category} preparation by {reduction_percentage}% to minimize waste"
                    )
        
        # General recommendations
        if not recommendations:
            recommendations.append("Monitor portion sizes to reduce waste")
            recommendations.append("Consider smaller batch sizes for unpopular items")
        
        return recommendations


# Convenience functions for direct use
def predict_demand_for_date(forecast_date: date, dining_hall: str, meal_type: str) -> Dict[str, Any]:
    """Predict demand for a specific date."""
    predictor = DemandPredictor()
    return predictor.predict_meal_demand(forecast_date, dining_hall, meal_type)


def predict_waste_for_date(forecast_date: date, dining_hall: str, meal_type: str) -> Dict[str, Any]:
    """Predict waste for a specific date."""
    predictor = WastePredictor()
    return predictor.predict_waste_by_category(forecast_date, dining_hall, meal_type)
