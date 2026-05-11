"""
Data loading utilities for GreenPlateAI.

This module provides classes and functions for loading and processing
various data formats including CSV, Excel, and JSON files.
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from datetime import datetime, date
from decimal import Decimal

from .validators import validate_file_extension, validate_file_size
from .helpers import clean_numeric_string, safe_json_loads
from .config import get_config

logger = logging.getLogger(__name__)


class DataLoader:
    """Base class for data loading operations."""
    
    def __init__(self, config=None):
        """Initialize data loader with configuration."""
        self.config = config or get_config()
        self.supported_formats = ['csv', 'xlsx', 'xls', 'json']
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file before loading.
        
        Args:
            file_path: Path to the file
            
        Returns:
            dict: Validation result
        """
        result = {
            'valid': True,
            'errors': [],
            'file_info': {}
        }
        
        # Check if file exists
        if not os.path.exists(file_path):
            result['valid'] = False
            result['errors'].append("File does not exist")
            return result
        
        # Get file info
        file_path_obj = Path(file_path)
        file_size = file_path_obj.stat().st_size
        file_extension = file_path_obj.suffix.lower().lstrip('.')
        
        result['file_info'] = {
            'name': file_path_obj.name,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'extension': file_extension
        }
        
        # Validate file extension
        if not validate_file_extension(file_path, self.supported_formats):
            result['valid'] = False
            result['errors'].append(f"Unsupported file format. Supported formats: {', '.join(self.supported_formats)}")
        
        # Validate file size
        if not validate_file_size(file_size, self.config.data_upload_max_size_mb):
            result['valid'] = False
            result['errors'].append(f"File size exceeds maximum allowed size of {self.config.data_upload_max_size_mb}MB")
        
        return result
    
    def load_file(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Load file based on its extension.
        
        Args:
            file_path: Path to the file
            **kwargs: Additional arguments for specific loaders
            
        Returns:
            DataFrame: Loaded data
        """
        # Validate file first
        validation_result = self.validate_file(file_path)
        if not validation_result['valid']:
            raise ValueError(f"File validation failed: {'; '.join(validation_result['errors'])}")
        
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        
        if file_extension == 'csv':
            return self.load_csv(file_path, **kwargs)
        elif file_extension in ['xlsx', 'xls']:
            return self.load_excel(file_path, **kwargs)
        elif file_extension == 'json':
            return self.load_json(file_path, **kwargs)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def load_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load CSV file."""
        default_kwargs = {
            'encoding': 'utf-8',
            'low_memory': False
        }
        default_kwargs.update(kwargs)
        
        try:
            df = pd.read_csv(file_path, **default_kwargs)
            logger.info(f"Successfully loaded CSV file: {file_path} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Failed to load CSV file {file_path}: {e}")
            raise
    
    def load_excel(self, file_path: str, sheet_name: Union[str, int] = 0, **kwargs) -> pd.DataFrame:
        """Load Excel file."""
        default_kwargs = {
            'sheet_name': sheet_name
        }
        default_kwargs.update(kwargs)
        
        try:
            df = pd.read_excel(file_path, **default_kwargs)
            logger.info(f"Successfully loaded Excel file: {file_path} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Failed to load Excel file {file_path}: {e}")
            raise
    
    def load_json(self, file_path: str, **kwargs) -> pd.DataFrame:
        """Load JSON file."""
        try:
            df = pd.read_json(file_path, **kwargs)
            logger.info(f"Successfully loaded JSON file: {file_path} ({len(df)} rows)")
            return df
        except Exception as e:
            logger.error(f"Failed to load JSON file {file_path}: {e}")
            raise


class CSVLoader(DataLoader):
    """Specialized CSV data loader."""
    
    def __init__(self, config=None):
        """Initialize CSV loader."""
        super().__init__(config)
    
    def detect_delimiter(self, file_path: str, sample_size: int = 1024) -> str:
        """
        Detect CSV delimiter automatically.
        
        Args:
            file_path: Path to CSV file
            sample_size: Number of bytes to sample for detection
            
        Returns:
            str: Detected delimiter
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sample = f.read(sample_size)
            
            # Common delimiters to test
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {}
            
            for delimiter in delimiters:
                delimiter_counts[delimiter] = sample.count(delimiter)
            
            # Return delimiter with highest count
            return max(delimiter_counts, key=delimiter_counts.get)
        except Exception as e:
            logger.warning(f"Failed to detect delimiter for {file_path}: {e}")
            return ','  # Default to comma
    
    def infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Infer column types from data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            dict: Column type mappings
        """
        column_types = {}
        
        for column in df.columns:
            series = df[column].dropna()
            
            if series.empty:
                column_types[column] = 'string'
                continue
            
            # Try to infer type
            try:
                # Numeric check
                pd.to_numeric(series)
                column_types[column] = 'numeric'
            except ValueError:
                # Date check
                try:
                    pd.to_datetime(series)
                    column_types[column] = 'datetime'
                except ValueError:
                    # Default to string
                    column_types[column] = 'string'
        
        return column_types
    
    def clean_csv_data(self, df: pd.DataFrame, column_types: Dict[str, str] = None) -> pd.DataFrame:
        """
        Clean and standardize CSV data.
        
        Args:
            df: DataFrame to clean
            column_types: Optional column type mappings
            
        Returns:
            DataFrame: Cleaned data
        """
        if column_types is None:
            column_types = self.infer_column_types(df)
        
        cleaned_df = df.copy()
        
        for column, col_type in column_types.items():
            if column not in cleaned_df.columns:
                continue
            
            if col_type == 'numeric':
                cleaned_df[column] = cleaned_df[column].apply(clean_numeric_string)
            elif col_type == 'datetime':
                cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors='coerce')
            elif col_type == 'string':
                cleaned_df[column] = cleaned_df[column].astype(str).str.strip()
        
        return cleaned_df
    
    def load_waste_data(self, file_path: str) -> pd.DataFrame:
        """
        Load and process waste data from CSV.
        
        Args:
            file_path: Path to waste data CSV
            
        Returns:
            DataFrame: Processed waste data
        """
        # Load with automatic delimiter detection
        delimiter = self.detect_delimiter(file_path)
        df = self.load_csv(file_path, delimiter=delimiter)
        
        # Standardize column names
        column_mapping = {
            'date': 'date',
            'food_item': 'food_item',
            'category': 'category',
            'source': 'source',
            'quantity_kg': 'quantity_kg',
            'cost': 'estimated_cost',
            'meal_period': 'meal_period',
            'dining_hall': 'dining_hall',
            'notes': 'notes'
        }
        
        # Rename columns (case-insensitive)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        df = df.rename(columns={k.lower(): v for k, v in column_mapping.items()})
        
        # Clean data
        df = self.clean_csv_data(df)
        
        # Validate required columns
        required_columns = ['date', 'food_item', 'quantity_kg']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Convert date column
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Calculate estimated cost if not provided
        if 'estimated_cost' not in df.columns or df['estimated_cost'].isna().all():
            df['estimated_cost'] = df['quantity_kg'] * 5.0  # Default $5/kg
        
        logger.info(f"Loaded waste data: {len(df)} records")
        return df
    
    def load_inventory_data(self, file_path: str) -> pd.DataFrame:
        """
        Load and process inventory data from CSV.
        
        Args:
            file_path: Path to inventory data CSV
            
        Returns:
            DataFrame: Processed inventory data
        """
        delimiter = self.detect_delimiter(file_path)
        df = self.load_csv(file_path, delimiter=delimiter)
        
        # Standardize column names
        column_mapping = {
            'food_item': 'food_item',
            'quantity': 'quantity',
            'batch_number': 'batch_number',
            'received_date': 'received_date',
            'expiration_date': 'expiration_date',
            'storage_location': 'storage_location',
            'cost_per_unit': 'cost_per_unit'
        }
        
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        df = df.rename(columns={k.lower(): v for k, v in column_mapping.items()})
        
        # Clean data
        df = self.clean_csv_data(df)
        
        # Validate required columns
        required_columns = ['food_item', 'quantity']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Convert date columns
        for date_col in ['received_date', 'expiration_date']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col]).dt.date
        
        logger.info(f"Loaded inventory data: {len(df)} records")
        return df


class ExcelLoader(DataLoader):
    """Specialized Excel data loader."""
    
    def __init__(self, config=None):
        """Initialize Excel loader."""
        super().__init__(config)
    
    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Get all sheet names from Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            list: Sheet names
        """
        try:
            excel_file = pd.ExcelFile(file_path)
            return excel_file.sheet_names
        except Exception as e:
            logger.error(f"Failed to read Excel sheets from {file_path}: {e}")
            raise
    
    def load_all_sheets(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        Load all sheets from Excel file.
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            dict: Dictionary of sheet names to DataFrames
        """
        try:
            all_sheets = pd.read_excel(file_path, sheet_name=None)
            logger.info(f"Loaded {len(all_sheets)} sheets from {file_path}")
            return all_sheets
        except Exception as e:
            logger.error(f"Failed to load Excel sheets from {file_path}: {e}")
            raise
    
    def load_sheet_by_name(self, file_path: str, sheet_name: str) -> pd.DataFrame:
        """
        Load specific sheet by name.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Name of sheet to load
            
        Returns:
            DataFrame: Sheet data
        """
        return self.load_excel(file_path, sheet_name=sheet_name)


class JSONLoader(DataLoader):
    """Specialized JSON data loader."""
    
    def __init__(self, config=None):
        """Initialize JSON loader."""
        super().__init__(config)
    
    def load_nested_json(self, file_path: str, normalize: bool = True) -> pd.DataFrame:
        """
        Load nested JSON data.
        
        Args:
            file_path: Path to JSON file
            normalize: Whether to normalize nested data
            
        Returns:
            DataFrame: Loaded data
        """
        try:
            if normalize:
                df = pd.json_normalize(pd.read_json(file_path))
            else:
                df = pd.read_json(file_path)
            
            logger.info(f"Loaded JSON data: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to load JSON data from {file_path}: {e}")
            raise
    
    def load_json_lines(self, file_path: str) -> pd.DataFrame:
        """
        Load JSON lines format (one JSON object per line).
        
        Args:
            file_path: Path to JSON lines file
            
        Returns:
            DataFrame: Loaded data
        """
        try:
            df = pd.read_json(file_path, lines=True)
            logger.info(f"Loaded JSON lines data: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Failed to load JSON lines data from {file_path}: {e}")
            raise


def create_data_loader(file_path: str, config=None) -> DataLoader:
    """
    Factory function to create appropriate data loader.
    
    Args:
        file_path: Path to the file
        config: Application configuration
        
    Returns:
        DataLoader: Appropriate data loader instance
    """
    file_extension = Path(file_path).suffix.lower().lstrip('.')
    
    if file_extension == 'csv':
        return CSVLoader(config)
    elif file_extension in ['xlsx', 'xls']:
        return ExcelLoader(config)
    elif file_extension == 'json':
        return JSONLoader(config)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")


def preview_data(file_path: str, max_rows: int = 10) -> Dict[str, Any]:
    """
    Preview data from file without full loading.
    
    Args:
        file_path: Path to the file
        max_rows: Maximum number of rows to preview
        
    Returns:
        dict: Preview information
    """
    try:
        loader = create_data_loader(file_path)
        
        # Validate file
        validation_result = loader.validate_file(file_path)
        if not validation_result['valid']:
            return {
                'success': False,
                'error': validation_result['errors']
            }
        
        # Load preview
        if isinstance(loader, CSVLoader):
            delimiter = loader.detect_delimiter(file_path)
            df = loader.load_csv(file_path, nrows=max_rows, delimiter=delimiter)
        elif isinstance(loader, ExcelLoader):
            sheet_names = loader.get_sheet_names(file_path)
            df = loader.load_excel(file_path, nrows=max_rows, sheet_name=sheet_names[0])
        else:  # JSON
            df = loader.load_json(file_path)
            df = df.head(max_rows)
        
        return {
            'success': True,
            'file_info': validation_result['file_info'],
            'preview': {
                'columns': df.columns.tolist(),
                'data': df.to_dict('records'),
                'total_rows': len(df),
                'data_types': df.dtypes.to_dict()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to preview data from {file_path}: {e}")
        return {
            'success': False,
            'error': str(e)
        }
