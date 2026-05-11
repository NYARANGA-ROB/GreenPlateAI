"""
Feature engineering for forecasting models in GreenPlateAI.

This module provides functions for extracting, transforming, and
engineering features from raw data for machine learning models.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple, Any
import logging
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from database.connection import get_session
from models.waste_record import WasteRecord
from models.food_item import FoodItem
from utils.helpers import convert_to_utc

logger = logging.getLogger(__name__)


def extract_features(df: pd.DataFrame, feature_config: Dict = None) -> pd.DataFrame:
    """
    Extract features from raw data DataFrame.
    
    Args:
        df: Raw data DataFrame
        feature_config: Configuration for feature extraction
        
    Returns:
        DataFrame: Features DataFrame
    """
    try:
        if df.empty:
            return pd.DataFrame()
        
        # Make a copy to avoid modifying original
        features_df = df.copy()
        
        # Ensure date column is datetime
        if 'date' in features_df.columns:
            features_df['date'] = pd.to_datetime(features_df['date'])
        
        # Extract temporal features
        features_df = extract_temporal_features(features_df)
        
        # Extract categorical features
        features_df = extract_categorical_features(features_df)
        
        # Extract statistical features
        features_df = extract_statistical_features(features_df)
        
        # Extract lag features
        features_df = extract_lag_features(features_df)
        
        # Extract rolling features
        features_df = extract_rolling_features(features_df)
        
        # Extract interaction features
        features_df = extract_interaction_features(features_df)
        
        logger.info(f"Extracted {len(features_df.columns)} features from {len(df)} records")
        return features_df
        
    except Exception as e:
        logger.error(f"Error extracting features: {e}")
        return pd.DataFrame()


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract temporal features from date column."""
    try:
        if 'date' not in df.columns:
            return df
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Basic temporal features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_year'] = df['date'].dt.dayofyear
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['quarter'] = df['date'].dt.quarter
        
        # Cyclical features
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        df['day_sin'] = np.sin(2 * np.pi * df['day'] / 31)
        df['day_cos'] = np.cos(2 * np.pi * df['day'] / 31)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Boolean features
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_month_start'] = (df['day'] == 1).astype(int)
        df['is_month_end'] = (df['day'] >= 28).astype(int)
        df['is_quarter_start'] = ((df['month'] % 3 == 1) & (df['day'] == 1)).astype(int)
        df['is_quarter_end'] = (df['month'] % 3 == 0).astype(int)
        
        # Special day features
        df['is_monday'] = (df['day_of_week'] == 0).astype(int)
        df['is_friday'] = (df['day_of_week'] == 4).astype(int)
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting temporal features: {e}")
        return df


def extract_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and encode categorical features."""
    try:
        df = df.copy()
        
        # Define categorical columns
        categorical_columns = ['category', 'source', 'meal_period', 'dining_hall']
        
        for col in categorical_columns:
            if col in df.columns:
                # Fill missing values
                df[col] = df[col].fillna('unknown')
                
                # Label encoding
                le = LabelEncoder()
                df[f'{col}_encoded'] = le.fit_transform(df[col])
                
                # One-hot encoding for low-cardinality features
                if df[col].nunique() <= 10:
                    dummies = pd.get_dummies(df[col], prefix=col)
                    df = pd.concat([df, dummies], axis=1)
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting categorical features: {e}")
        return df


def extract_statistical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract statistical features from numerical columns."""
    try:
        df = df.copy()
        
        if 'quantity_kg' not in df.columns:
            return df
        
        # Log transformations
        df['quantity_log'] = np.log1p(df['quantity_kg'])
        df['quantity_sqrt'] = np.sqrt(df['quantity_kg'])
        
        # Binning
        df['quantity_bin'] = pd.cut(df['quantity_kg'], bins=5, labels=False)
        
        # Z-score
        if len(df) > 1:
            mean_qty = df['quantity_kg'].mean()
            std_qty = df['quantity_kg'].std()
            if std_qty > 0:
                df['quantity_zscore'] = (df['quantity_kg'] - mean_qty) / std_qty
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting statistical features: {e}")
        return df


def extract_lag_features(df: pd.DataFrame, lags: List[int] = None) -> pd.DataFrame:
    """Extract lag features for time series."""
    try:
        if lags is None:
            lags = [1, 2, 3, 7, 14, 30]
        
        df = df.copy()
        
        if 'date' not in df.columns or 'quantity_kg' not in df.columns:
            return df
        
        # Sort by date
        df = df.sort_values('date')
        
        for lag in lags:
            df[f'quantity_lag_{lag}'] = df['quantity_kg'].shift(lag)
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting lag features: {e}")
        return df


def extract_rolling_features(df: pd.DataFrame, windows: List[int] = None) -> pd.DataFrame:
    """Extract rolling window features."""
    try:
        if windows is None:
            windows = [3, 7, 14, 30]
        
        df = df.copy()
        
        if 'quantity_kg' not in df.columns:
            return df
        
        # Sort by date for rolling calculations
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        for window in windows:
            # Rolling mean
            df[f'quantity_rolling_mean_{window}'] = df['quantity_kg'].rolling(window=window).mean()
            
            # Rolling std
            df[f'quantity_rolling_std_{window}'] = df['quantity_kg'].rolling(window=window).std()
            
            # Rolling min/max
            df[f'quantity_rolling_min_{window}'] = df['quantity_kg'].rolling(window=window).min()
            df[f'quantity_rolling_max_{window}'] = df['quantity_kg'].rolling(window=window).max()
            
            # Rolling sum
            df[f'quantity_rolling_sum_{window}'] = df['quantity_kg'].rolling(window=window).sum()
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting rolling features: {e}")
        return df


def extract_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract interaction features between variables."""
    try:
        df = df.copy()
        
        # Temporal interactions
        if 'day_of_week' in df.columns and 'month' in df.columns:
            df['dow_month_interaction'] = df['day_of_week'] * df['month']
        
        # Category interactions
        if 'category_encoded' in df.columns and 'source_encoded' in df.columns:
            df['category_source_interaction'] = df['category_encoded'] * df['source_encoded']
        
        # Quantity interactions
        if 'quantity_kg' in df.columns and 'day_of_week' in df.columns:
            df['quantity_dow_interaction'] = df['quantity_kg'] * df['day_of_week']
        
        return df
        
    except Exception as e:
        logger.error(f"Error extracting interaction features: {e}")
        return df


def prepare_training_data(
    start_date: date,
    end_date: date,
    target_column: str = 'quantity_kg'
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare training data with features and target.
    
    Args:
        start_date: Start date for data
        end_date: End date for data
        target_column: Target variable column
        
    Returns:
        tuple: (features DataFrame, target Series)
    """
    try:
        # Get raw data
        raw_data = get_historical_data(start_date, end_date)
        
        if raw_data.empty:
            return pd.DataFrame(), pd.Series()
        
        # Extract features
        features_df = extract_features(raw_data)
        
        # Separate features and target
        if target_column not in features_df.columns:
            raise ValueError(f"Target column '{target_column}' not found")
        
        target = features_df[target_column]
        features = features_df.drop(columns=[target_column, 'date'])
        
        # Remove columns with too many missing values
        missing_threshold = 0.5
        features = features.drop(columns=features.columns[features.isnull().mean() > missing_threshold])
        
        # Fill remaining missing values
        features = features.fillna(features.median())
        
        logger.info(f"Prepared training data: {len(features)} samples, {len(features.columns)} features")
        return features, target
        
    except Exception as e:
        logger.error(f"Error preparing training data: {e}")
        return pd.DataFrame(), pd.Series()


def create_feature_matrix(
    dates: List[date],
    meal_period: str = None,
    dining_hall: str = None,
    category: str = None
) -> pd.DataFrame:
    """
    Create feature matrix for prediction dates.
    
    Args:
        dates: List of dates to create features for
        meal_period: Meal period filter
        dining_hall: Dining hall filter
        category: Category filter
        
    Returns:
        DataFrame: Feature matrix
    """
    try:
        features_list = []
        
        for target_date in dates:
            features = {
                'date': target_date,
                'meal_period': meal_period,
                'dining_hall': dining_hall,
                'category': category
            }
            
            # Extract temporal features
            features.update({
                'year': target_date.year,
                'month': target_date.month,
                'day': target_date.day,
                'day_of_week': target_date.weekday(),
                'day_of_year': target_date.timetuple().tm_yday,
                'week_of_year': target_date.isocalendar()[1],
                'quarter': (target_date.month - 1) // 3 + 1,
                'is_weekend': int(target_date.weekday() >= 5),
                'is_month_start': int(target_date.day == 1),
                'is_month_end': int(target_date.day >= 28)
            })
            
            # Cyclical features
            features.update({
                'month_sin': np.sin(2 * np.pi * target_date.month / 12),
                'month_cos': np.cos(2 * np.pi * target_date.month / 12),
                'day_sin': np.sin(2 * np.pi * target_date.day / 31),
                'day_cos': np.cos(2 * np.pi * target_date.day / 31),
                'dow_sin': np.sin(2 * np.pi * target_date.weekday() / 7),
                'dow_cos': np.cos(2 * np.pi * target_date.weekday() / 7)
            })
            
            features_list.append(features)
        
        df = pd.DataFrame(features_list)
        
        # Extract categorical features
        df = extract_categorical_features(df)
        
        return df
        
    except Exception as e:
        logger.error(f"Error creating feature matrix: {e}")
        return pd.DataFrame()


def feature_engineering_pipeline() -> Pipeline:
    """
    Create a scikit-learn pipeline for feature engineering.
    
    Returns:
        Pipeline: Feature engineering pipeline
    """
    try:
        # Define preprocessing for different column types
        numeric_features = ['year', 'month', 'day', 'day_of_week', 'day_of_year']
        categorical_features = ['category_encoded', 'source_encoded']
        
        numeric_transformer = StandardScaler()
        
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
                ('cat', 'passthrough', categorical_features)
            ]
        )
        
        # Create pipeline
        pipeline = Pipeline(steps=[
            ('preprocessor', preprocessor)
        ])
        
        return pipeline
        
    except Exception as e:
        logger.error(f"Error creating feature engineering pipeline: {e}")
        return None


def get_feature_importance(model, feature_names: List[str]) -> Dict[str, float]:
    """
    Get feature importance from trained model.
    
    Args:
        model: Trained ML model
        feature_names: List of feature names
        
    Returns:
        dict: Feature importance mapping
    """
    try:
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importances = np.abs(model.coef_)
        else:
            return {}
        
        # Create importance mapping
        importance_dict = {}
        for name, importance in zip(feature_names, importances):
            importance_dict[name] = float(importance)
        
        # Sort by importance
        sorted_importance = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
        
        return sorted_importance
        
    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        return {}


def select_top_features(
    features_df: pd.DataFrame,
    target: pd.Series,
    method: str = 'correlation',
    top_k: int = 20
) -> List[str]:
    """
    Select top features based on various methods.
    
    Args:
        features_df: Features DataFrame
        target: Target variable
        method: Selection method ('correlation', 'mutual_info', 'variance')
        top_k: Number of top features to select
        
    Returns:
        list: Selected feature names
    """
    try:
        if method == 'correlation':
            # Calculate correlation with target
            correlations = []
            for col in features_df.columns:
                if features_df[col].dtype in ['int64', 'float64']:
                    corr = features_df[col].corr(target)
                    correlations.append((col, abs(corr)))
            
            # Sort by correlation
            correlations.sort(key=lambda x: x[1], reverse=True)
            return [col for col, _ in correlations[:top_k]]
        
        elif method == 'variance':
            # Select features with highest variance
            variances = features_df.var()
            top_features = variances.nlargest(top_k).index.tolist()
            return top_features
        
        else:
            # Default to all features
            return features_df.columns.tolist()[:top_k]
        
    except Exception as e:
        logger.error(f"Error selecting top features: {e}")
        return []


def validate_features(features_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate extracted features.
    
    Args:
        features_df: Features DataFrame
        
    Returns:
        dict: Validation results
    """
    try:
        validation_results = {
            'valid': True,
            'issues': [],
            'statistics': {}
        }
        
        # Check for empty DataFrame
        if features_df.empty:
            validation_results['valid'] = False
            validation_results['issues'].append("Features DataFrame is empty")
            return validation_results
        
        # Check for missing values
        missing_counts = features_df.isnull().sum()
        high_missing = missing_counts[missing_counts > len(features_df) * 0.5]
        
        if not high_missing.empty:
            validation_results['issues'].append(f"High missing values in: {high_missing.index.tolist()}")
        
        # Check for constant features
        constant_features = []
        for col in features_df.columns:
            if features_df[col].dtype in ['int64', 'float64']:
                if features_df[col].var() == 0:
                    constant_features.append(col)
        
        if constant_features:
            validation_results['issues'].append(f"Constant features: {constant_features}")
        
        # Statistics
        validation_results['statistics'] = {
            'total_samples': len(features_df),
            'total_features': len(features_df.columns),
            'missing_values': missing_counts.sum(),
            'numeric_features': len(features_df.select_dtypes(include=[np.number]).columns),
            'categorical_features': len(features_df.select_dtypes(include=['object']).columns)
        }
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Error validating features: {e}")
        return {'valid': False, 'issues': [str(e)]}


# Helper functions

def get_historical_data(start_date: date, end_date: date) -> pd.DataFrame:
    """Get historical data for feature extraction."""
    try:
        db = get_session()
        
        records = db.query(WasteRecord).filter(
            WasteRecord.date >= start_date,
            WasteRecord.date <= end_date,
            WasteRecord.is_active == True
        ).all()
        
        data = []
        for record in records:
            data.append({
                'date': record.date,
                'quantity_kg': float(record.quantity_kg),
                'category': record.category,
                'source': record.source,
                'meal_period': record.meal_period,
                'dining_hall': record.dining_hall,
                'estimated_cost': float(record.estimated_cost or 0)
            })
        
        df = pd.DataFrame(data)
        db.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        return pd.DataFrame()
