"""
Data preprocessing utilities for AI forecasting system.

This module provides comprehensive data preprocessing, cleaning,
and feature engineering for demand and waste forecasting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from pathlib import Path
import json

from database.connection import get_session
from database.models import FoodWasteLog, MealLog, User, MealType, WasteCategory

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """Data preprocessing for forecasting models."""
    
    def __init__(self):
        """Initialize the data preprocessor."""
        self.session = get_session()
        self.data_cache = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=1)
    
    def get_historical_data(self, start_date: date = None, end_date: date = None) -> pd.DataFrame:
        """Get historical data for forecasting."""
        cache_key = f"historical_{start_date}_{end_date}"
        
        # Check cache
        if self._is_cache_valid(cache_key):
            logger.info("Using cached historical data")
            return self.data_cache[cache_key]
        
        logger.info("Fetching historical data from database")
        
        # Set default date range
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=365)  # Last year by default
        
        # Query meal logs
        meal_logs = self.session.query(MealLog).filter(
            MealLog.meal_date >= start_date,
            MealLog.meal_date <= end_date,
            MealLog.is_active == True
        ).all()
        
        # Query waste logs
        waste_logs = self.session.query(FoodWasteLog).filter(
            FoodWasteLog.waste_date >= start_date,
            FoodWasteLog.waste_date <= end_date,
            FoodWasteLog.is_active == True
        ).all()
        
        # Convert to DataFrames
        meal_data = []
        for log in meal_logs:
            meal_data.append({
                'date': log.meal_date,
                'meal_type': log.meal_type.value,
                'dining_hall': log.dining_hall,
                'calories': log.calories or 0,
                'protein': log.protein or 0,
                'carbs': log.carbs or 0,
                'fat': log.fat or 0,
                'fiber': log.fiber or 0,
                'satisfaction_rating': log.satisfaction_rating or 0,
                'portion_size_rating': log.portion_size_rating or 0,
                'taste_rating': log.taste_rating or 0,
                'meal_items': log.meal_items or {},
                'user_id': log.user_id
            })
        
        waste_data = []
        for log in waste_logs:
            waste_data.append({
                'date': log.waste_date,
                'meal_type': log.meal_period.value if log.meal_period else 'unknown',
                'dining_hall': log.dining_hall,
                'food_item': log.food_item,
                'category': log.category,
                'waste_category': log.waste_category.value,
                'quantity': log.quantity_kg,
                'estimated_cost': log.estimated_cost or 0,
                'reason': log.reason or '',
                'temperature': log.temperature or 0,
                'co2_equivalent': log.co2_equivalent_kg or 0,
                'water_footprint': log.water_footprint_liters or 0,
                'land_use': log.land_use_m2 or 0,
                'food_quality_rating': log.food_quality_rating or 0,
                'appearance_rating': log.appearance_rating or 0,
                'recorded_by': log.recorded_by or ''
            })
        
        meal_df = pd.DataFrame(meal_data)
        waste_df = pd.DataFrame(waste_data)
        
        # Combine data
        combined_df = self._combine_meal_waste_data(meal_df, waste_df)
        
        # Cache the result
        self.data_cache[cache_key] = combined_df
        self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
        
        logger.info(f"Retrieved {len(combined_df)} records from {start_date} to {end_date}")
        
        return combined_df
    
    def _combine_meal_waste_data(self, meal_df: pd.DataFrame, waste_df: pd.DataFrame) -> pd.DataFrame:
        """Combine meal and waste data."""
        # Create demand data from meal logs
        if not meal_df.empty:
            # Aggregate meal data by date, meal_type, dining_hall
            meal_agg = meal_df.groupby(['date', 'meal_type', 'dining_hall']).agg({
                'calories': 'sum',
                'protein': 'sum',
                'carbs': 'sum',
                'fat': 'sum',
                'fiber': 'sum',
                'satisfaction_rating': 'mean',
                'portion_size_rating': 'mean',
                'taste_rating': 'mean',
                'user_id': 'count'
            }).reset_index()
            
            meal_agg.rename(columns={'user_id': 'meal_count'}, inplace=True)
            meal_agg['demand'] = meal_agg['meal_count']  # Use meal count as demand proxy
        else:
            meal_agg = pd.DataFrame()
        
        # Aggregate waste data
        if not waste_df.empty:
            waste_agg = waste_df.groupby(['date', 'meal_type', 'dining_hall']).agg({
                'quantity': 'sum',
                'estimated_cost': 'sum',
                'co2_equivalent': 'sum',
                'water_footprint': 'sum',
                'land_use': 'sum',
                'food_quality_rating': 'mean',
                'appearance_rating': 'mean',
                'food_item': 'count'
            }).reset_index()
            
            waste_agg.rename(columns={'food_item': 'waste_items_count'}, inplace=True)
        else:
            waste_agg = pd.DataFrame()
        
        # Merge meal and waste data
        if not meal_agg.empty and not waste_agg.empty:
            combined_df = pd.merge(
                meal_agg, waste_agg,
                on=['date', 'meal_type', 'dining_hall'],
                how='outer'
            )
        elif not meal_agg.empty:
            combined_df = meal_agg
            combined_df['quantity'] = 0
            combined_df['estimated_cost'] = 0
            combined_df['co2_equivalent'] = 0
            combined_df['water_footprint'] = 0
            combined_df['land_use'] = 0
            combined_df['waste_items_count'] = 0
        elif not waste_agg.empty:
            combined_df = waste_agg
            combined_df['demand'] = 0
            combined_df['calories'] = 0
            combined_df['protein'] = 0
            combined_df['carbs'] = 0
            combined_df['fat'] = 0
            combined_df['fiber'] = 0
            combined_df['satisfaction_rating'] = 0
            combined_df['portion_size_rating'] = 0
            combined_df['taste_rating'] = 0
            combined_df['meal_count'] = 0
        else:
            combined_df = pd.DataFrame()
        
        return combined_df
    
    def add_external_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add external features like weather, events, student population."""
        logger.info("Adding external features")
        
        df = df.copy()
        
        # Add weather features
        df = self._add_weather_features(df)
        
        # Add academic calendar features
        df = self._add_academic_features(df)
        
        # Add event features
        df = self._add_event_features(df)
        
        # Add student population features
        df = self._add_student_population_features(df)
        
        # Add holiday features
        df = self._add_holiday_features(df)
        
        return df
    
    def _add_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add weather-related features."""
        # For demo purposes, we'll add synthetic weather data
        # In production, this would fetch from a weather API
        
        if 'date' in df.columns:
            # Generate synthetic weather data
            np.random.seed(42)  # For reproducibility
            
            # Temperature varies by season
            df['temperature'] = df['date'].apply(self._get_temperature)
            df['humidity'] = np.random.uniform(40, 80, len(df))
            df['precipitation'] = np.random.exponential(2, len(df))
            df['wind_speed'] = np.random.uniform(5, 25, len(df))
            
            # Weather conditions
            df['is_rainy'] = (df['precipitation'] > 2).astype(int)
            df['is_hot'] = (df['temperature'] > 25).astype(int)
            df['is_cold'] = (df['temperature'] < 10).astype(int)
        
        return df
    
    def _get_temperature(self, date_obj) -> float:
        """Get synthetic temperature based on date."""
        # Simple seasonal temperature model
        day_of_year = date_obj.timetuple().tm_yday
        base_temp = 15 + 10 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        noise = np.random.normal(0, 3)
        return base_temp + noise
    
    def _add_academic_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add academic calendar features."""
        if 'date' in df.columns:
            df['is_exam_period'] = df['date'].apply(self._is_exam_period)
            df['is_break_period'] = df['date'].apply(self._is_break_period)
            df['is_registration_period'] = df['date'].apply(self._is_registration_period)
            df['is_graduation_period'] = df['date'].apply(self._is_graduation_period)
            df['academic_week'] = df['date'].apply(self._get_academic_week)
        
        return df
    
    def _is_exam_period(self, date_obj) -> int:
        """Check if date is during exam period."""
        # Simplified exam periods (mid-December and mid-May)
        month, day = date_obj.month, date_obj.day
        return int((month == 12 and 10 <= day <= 20) or (month == 5 and 10 <= day <= 20))
    
    def _is_break_period(self, date_obj) -> int:
        """Check if date is during break period."""
        # Winter break, spring break, summer break
        month, day = date_obj.month, date_obj.day
        return int(
            (month == 12 and day >= 20) or (month == 1 and day <= 15) or  # Winter break
            (month == 3 and 10 <= day <= 20) or  # Spring break
            (month in [6, 7, 8])  # Summer break
        )
    
    def _is_registration_period(self, date_obj) -> int:
        """Check if date is during registration period."""
        # Registration periods (late August, early January)
        month, day = date_obj.month, date_obj.day
        return int((month == 8 and 20 <= day <= 31) or (month == 1 and 1 <= day <= 15))
    
    def _is_graduation_period(self, date_obj) -> int:
        """Check if date is during graduation period."""
        # Graduation periods (mid-May, mid-December)
        month, day = date_obj.month, date_obj.day
        return int((month == 5 and 15 <= day <= 25) or (month == 12 and 15 <= day <= 25))
    
    def _get_academic_week(self, date_obj) -> int:
        """Get academic week number."""
        # Simplified academic calendar
        year_start = date(date_obj.year, 9, 1)  # Academic year starts Sept 1
        if date_obj < year_start:
            year_start = date(date_obj.year - 1, 9, 1)
        
        return ((date_obj - year_start).days // 7) + 1
    
    def _add_event_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add event-related features."""
        if 'date' in df.columns:
            # For demo purposes, we'll add some synthetic events
            df['has_event'] = df['date'].apply(self._has_event)
            df['event_type'] = df['date'].apply(self._get_event_type)
            df['is_sports_event'] = df['date'].apply(self._is_sports_event)
            df['is_cultural_event'] = df['date'].apply(self._is_cultural_event)
        
        return df
    
    def _has_event(self, date_obj) -> int:
        """Check if there's an event on this date."""
        # Random events for demo (about 10% of days have events)
        np.random.seed(date_obj.toordinal())
        return int(np.random.random() < 0.1)
    
    def _get_event_type(self, date_obj) -> str:
        """Get event type for date."""
        np.random.seed(date_obj.toordinal())
        event_types = ['sports', 'cultural', 'academic', 'social', 'none']
        return event_types[int(np.random.random() * len(event_types))]
    
    def _is_sports_event(self, date_obj) -> int:
        """Check if there's a sports event."""
        np.random.seed(date_obj.toordinal() + 1)
        return int(np.random.random() < 0.05)  # 5% chance
    
    def _is_cultural_event(self, date_obj) -> int:
        """Check if there's a cultural event."""
        np.random.seed(date_obj.toordinal() + 2)
        return int(np.random.random() < 0.03)  # 3% chance
    
    def _add_student_population_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add student population features."""
        if 'date' in df.columns:
            # Base student population varies by semester
            df['student_count'] = df['date'].apply(self._get_student_count)
            df['student_density'] = df['student_count'] / 10000  # Normalized
            df['is_peak_student_period'] = df['date'].apply(self._is_peak_student_period)
        
        return df
    
    def _get_student_count(self, date_obj) -> int:
        """Get estimated student count for date."""
        # Student population varies by semester
        month = date_obj.month
        if month in [9, 10, 11, 12, 1, 2, 3, 4, 5]:  # Academic year
            base_count = 15000
        else:  # Summer
            base_count = 3000
        
        # Add some variation
        np.random.seed(date_obj.toordinal())
        variation = np.random.normal(0, 500)
        return int(base_count + variation)
    
    def _is_peak_student_period(self, date_obj) -> int:
        """Check if it's a peak student period."""
        month = date_obj.month
        return int(month in [9, 10, 1, 2])  # Fall and spring semesters
    
    def _add_holiday_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add holiday-related features."""
        if 'date' in df.columns:
            df['is_holiday'] = df['date'].apply(self._is_holiday)
            df['is_pre_holiday'] = df['date'].apply(self._is_pre_holiday)
            df['is_post_holiday'] = df['date'].apply(self._is_post_holiday)
            df['days_to_next_holiday'] = df['date'].apply(self._days_to_next_holiday)
        
        return df
    
    def _is_holiday(self, date_obj) -> int:
        """Check if date is a holiday."""
        # Major holidays (simplified)
        month, day = date_obj.month, date_obj.day
        holidays = [
            (1, 1),   # New Year
            (1, 15),  # MLK Day
            (2, 14),  # Valentine's Day
            (3, 17),  # St. Patrick's Day
            (4, 1),   # April Fool's
            (5, 25),  # Memorial Day
            (7, 4),   # Independence Day
            (9, 5),   # Labor Day
            (10, 31), # Halloween
            (11, 11), # Veterans Day
            (11, 23), # Thanksgiving
            (12, 25), # Christmas
        ]
        
        return int((month, day) in holidays)
    
    def _is_pre_holiday(self, date_obj) -> int:
        """Check if date is before a holiday."""
        # Check if tomorrow is a holiday
        tomorrow = date_obj + timedelta(days=1)
        return self._is_holiday(tomorrow)
    
    def _is_post_holiday(self, date_obj) -> int:
        """Check if date is after a holiday."""
        # Check if yesterday was a holiday
        yesterday = date_obj - timedelta(days=1)
        return self._is_holiday(yesterday)
    
    def _days_to_next_holiday(self, date_obj) -> int:
        """Calculate days to next holiday."""
        # Simplified - just return a random number for demo
        np.random.seed(date_obj.toordinal())
        return int(np.random.random() * 30)
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and preprocess the data."""
        logger.info(f"Cleaning data with {len(df)} records")
        
        if df.empty:
            return df
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Handle missing values
        df = self._handle_missing_values(df)
        
        # Handle outliers
        df = self._handle_outliers(df)
        
        # Validate data types
        df = self._validate_data_types(df)
        
        # Remove invalid records
        df = self._remove_invalid_records(df)
        
        logger.info(f"Data cleaned. {len(df)} records remaining")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset."""
        # For numeric columns, fill with median
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            if df[col].isnull().sum() > 0:
                median_value = df[col].median()
                df[col] = df[col].fillna(median_value)
        
        # For categorical columns, fill with mode
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            if df[col].isnull().sum() > 0:
                mode_value = df[col].mode()
                if len(mode_value) > 0:
                    df[col] = df[col].fillna(mode_value[0])
                else:
                    df[col] = df[col].fillna('unknown')
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle outliers in numeric columns."""
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in ['date']:  # Skip date column
                continue
            
            # Calculate IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define outlier bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Cap outliers (winsorization)
            df[col] = df[col].clip(lower_bound, upper_bound)
        
        return df
    
    def _validate_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and correct data types."""
        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # Ensure numeric columns are numeric
        numeric_columns = [
            'demand', 'quantity', 'estimated_cost', 'calories', 'protein',
            'carbs', 'fat', 'fiber', 'temperature', 'humidity', 'precipitation',
            'wind_speed', 'student_count', 'co2_equivalent', 'water_footprint', 'land_use'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _remove_invalid_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove invalid or inconsistent records."""
        if df.empty:
            return df
        
        # Remove records with negative quantities or costs
        if 'quantity' in df.columns:
            df = df[df['quantity'] >= 0]
        
        if 'estimated_cost' in df.columns:
            df = df[df['estimated_cost'] >= 0]
        
        if 'demand' in df.columns:
            df = df[df['demand'] >= 0]
        
        # Remove records with unrealistic values
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= -50) & (df['temperature'] <= 50)]
        
        if 'humidity' in df.columns:
            df = df[(df['humidity'] >= 0) & (df['humidity'] <= 100)]
        
        return df
    
    def create_training_datasets(self, df: pd.DataFrame, target_column: str, 
                               test_size: float = 0.2, validation_size: float = 0.1) -> Dict[str, Any]:
        """Create training, validation, and test datasets."""
        logger.info(f"Creating training datasets for {target_column}")
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Remove rows with missing target
        df = df.dropna(subset=[target_column])
        
        # Calculate split points
        n_samples = len(df)
        test_samples = int(n_samples * test_size)
        validation_samples = int(n_samples * validation_size)
        train_samples = n_samples - test_samples - validation_samples
        
        # Split data
        train_df = df.iloc[:train_samples]
        val_df = df.iloc[train_samples:train_samples + validation_samples]
        test_df = df.iloc[train_samples + validation_samples:]
        
        datasets = {
            'train': train_df,
            'validation': val_df,
            'test': test_df,
            'target_column': target_column,
            'feature_columns': [col for col in df.columns if col != target_column and col != 'date'],
            'split_info': {
                'total_samples': n_samples,
                'train_samples': train_samples,
                'validation_samples': validation_samples,
                'test_samples': test_samples,
                'train_ratio': train_samples / n_samples,
                'validation_ratio': validation_samples / n_samples,
                'test_ratio': test_samples / n_samples
            }
        }
        
        logger.info(f"Datasets created: Train={train_samples}, Val={validation_samples}, Test={test_samples}")
        
        return datasets
    
    def prepare_time_series_data(self, df: pd.DataFrame, target_column: str, 
                               forecast_horizon: int = 7) -> Dict[str, Any]:
        """Prepare data for time series forecasting."""
        logger.info(f"Preparing time series data for {target_column}")
        
        # Ensure data is sorted by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Create time series dataset
        ts_data = {
            'dates': df['date'].values,
            'values': df[target_column].values,
            'exogenous_features': {}
        }
        
        # Add exogenous features (all other columns except date and target)
        feature_columns = [col for col in df.columns if col not in ['date', target_column]]
        
        for col in feature_columns:
            ts_data['exogenous_features'][col] = df[col].values
        
        # Create sequences for time series
        sequences = self._create_sequences(df, target_column, forecast_horizon)
        
        ts_data.update({
            'sequences': sequences,
            'forecast_horizon': forecast_horizon,
            'n_samples': len(df)
        })
        
        return ts_data
    
    def _create_sequences(self, df: pd.DataFrame, target_column: str, 
                         forecast_horizon: int, sequence_length: int = 30) -> Dict[str, np.ndarray]:
        """Create sequences for time series forecasting."""
        values = df[target_column].values
        
        X, y = [], []
        
        for i in range(len(values) - sequence_length - forecast_horizon + 1):
            # Input sequence
            X.append(values[i:i + sequence_length])
            # Output sequence
            y.append(values[i + sequence_length:i + sequence_length + forecast_horizon])
        
        return {
            'X': np.array(X),
            'y': np.array(y),
            'sequence_length': sequence_length,
            'forecast_horizon': forecast_horizon
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is valid."""
        if cache_key not in self.data_cache:
            return False
        
        if cache_key not in self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry[cache_key]
    
    def clear_cache(self):
        """Clear all cached data."""
        self.data_cache.clear()
        self.cache_expiry.clear()
        logger.info("Cache cleared")
    
    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of the data."""
        if df.empty:
            return {'error': 'No data available'}
        
        summary = {
            'shape': df.shape,
            'columns': list(df.columns),
            'data_types': df.dtypes.to_dict(),
            'missing_values': df.isnull().sum().to_dict(),
            'numeric_summary': df.describe().to_dict(),
            'date_range': None,
            'unique_values': {}
        }
        
        # Date range
        if 'date' in df.columns:
            summary['date_range'] = {
                'start': df['date'].min().isoformat(),
                'end': df['date'].max().isoformat(),
                'days': (df['date'].max() - df['date'].min()).days
            }
        
        # Unique values for categorical columns
        categorical_columns = df.select_dtypes(include=['object']).columns
        for col in categorical_columns:
            summary['unique_values'][col] = df[col].nunique()
        
        return summary
    
    def export_processed_data(self, df: pd.DataFrame, filename: str = None) -> str:
        """Export processed data to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"processed_data_{timestamp}.csv"
        
        filepath = Path("data/processed")
        filepath.mkdir(parents=True, exist_ok=True)
        filepath = filepath / filename
        
        df.to_csv(filepath, index=False)
        
        logger.info(f"Processed data exported to {filepath}")
        return str(filepath)


# Convenience functions for direct use
def get_forecasting_data(start_date: date = None, end_date: date = None) -> pd.DataFrame:
    """Get forecasting data."""
    preprocessor = DataPreprocessor()
    return preprocessor.get_historical_data(start_date, end_date)


def preprocess_forecasting_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess forecasting data."""
    preprocessor = DataPreprocessor()
    return preprocessor.clean_data(preprocessor.add_external_features(df))
