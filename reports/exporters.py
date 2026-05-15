"""
Data export utilities for GreenPlateAI reports.
This module provides functions for exporting data and reports
to various formats including CSV, Excel, PDF, and JSON.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Union
import logging
from io import BytesIO
import json
import base64

logger = logging.getLogger(__name__)


def export_to_csv(
    data: Union[pd.DataFrame, List[Dict], Dict],
    filename: str = None,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Export data to CSV format.
    
    Args:
        data: Data to export (DataFrame, list of dicts, or dict)
        filename: Output filename
        include_metadata: Whether to include metadata
        
    Returns:
        dict: Export result with file info
    """
    try:
        # Convert data to DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.csv"
        
        # Add metadata if requested
        if include_metadata and 'metadata' not in df.columns:
            metadata_row = {
                'export_timestamp': datetime.now(),
                'total_records': len(df),
                'export_format': 'CSV'
            }
            # Add metadata as first row
            df = pd.concat([pd.DataFrame([metadata_row]), df], ignore_index=True)
        
        # Create CSV content
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        csv_content = csv_buffer.getvalue()
        
        # Encode for web display
        csv_base64 = base64.b64encode(csv_content).decode()
        
        result = {
            'success': True,
            'filename': filename,
            'format': 'CSV',
            'size_bytes': len(csv_content),
            'records_count': len(df),
            'download_url': f"data:text/csv;base64,{csv_base64}",
            'content': csv_content.decode('utf-8') if isinstance(csv_content, bytes) else csv_content
        }
        
        logger.info(f"Successfully exported {len(df)} records to CSV: {filename}")
        return result
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return {
            'success': False,
            'error': str(e),
            'format': 'CSV'
        }


def export_to_excel(
    data: Union[pd.DataFrame, List[Dict], Dict],
    filename: str = None,
    sheet_name: str = "Data",
    include_metadata: bool = True,
    include_charts: bool = False
) -> Dict[str, Any]:
    """
    Export data to Excel format.
    
    Args:
        data: Data to export
        filename: Output filename
        sheet_name: Excel sheet name
        include_metadata: Whether to include metadata
        include_charts: Whether to include charts
        
    Returns:
        dict: Export result with file info
    """
    try:
        # Convert data to DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.xlsx"
        
        # Create Excel writer
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Add metadata sheet if requested
            if include_metadata:
                metadata_data = {
                    'Export Timestamp': [datetime.now()],
                    'Total Records': [len(df)],
                    'Export Format': ['Excel'],
                    'Sheet Name': [sheet_name]
                }
                metadata_df = pd.DataFrame(metadata_data)
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Add main data sheet
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add summary sheet if data is large
            if len(df) > 100:
                summary_df = df.describe(include='all').transpose()
                summary_df.to_excel(writer, sheet_name='Summary', index=True)
        
        excel_content = excel_buffer.getvalue()
        
        # Encode for web display
        excel_base64 = base64.b64encode(excel_content).decode()
        
        result = {
            'success': True,
            'filename': filename,
            'format': 'Excel',
            'size_bytes': len(excel_content),
            'records_count': len(df),
            'download_url': f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{excel_base64}",
            'sheets': [sheet_name] + (['Metadata', 'Summary'] if include_metadata else [])
        }
        
        logger.info(f"Successfully exported {len(df)} records to Excel: {filename}")
        return result
        
    except Exception as e:
        logger.error(f"Error exporting to Excel: {e}")
        return {
            'success': False,
            'error': str(e),
            'format': 'Excel'
        }


def export_to_pdf(
    data: Union[pd.DataFrame, List[Dict], Dict],
    filename: str = None,
    title: str = "Report",
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Export data to PDF format.
    
    Args:
        data: Data to export
        filename: Output filename
        title: Document title
        include_metadata: Whether to include metadata
        
    Returns:
        dict: Export result with file info
    """
    try:
        # Convert data to DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.pdf"
        
        # Create PDF content (simplified version)
        # In a real implementation, you'd use reportlab or similar
        pdf_content = create_simple_pdf(df, title, include_metadata)
        
        # Encode for web display
        pdf_base64 = base64.b64encode(pdf_content).decode()
        
        result = {
            'success': True,
            'filename': filename,
            'format': 'PDF',
            'size_bytes': len(pdf_content),
            'records_count': len(df),
            'download_url': f"data:application/pdf;base64,{pdf_base64}",
            'title': title
        }
        
        logger.info(f"Successfully exported {len(df)} records to PDF: {filename}")
        return result
        
    except Exception as e:
        logger.error(f"Error exporting to PDF: {e}")
        return {
            'success': False,
            'error': str(e),
            'format': 'PDF'
        }


def export_to_json(
    data: Union[pd.DataFrame, List[Dict], Dict],
    filename: str = None,
    pretty_print: bool = True,
    include_metadata: bool = True
) -> Dict[str, Any]:
    """
    Export data to JSON format.
    
    Args:
        data: Data to export
        filename: Output filename
        pretty_print: Whether to format JSON nicely
        include_metadata: Whether to include metadata
        
    Returns:
        dict: Export result with file info
    """
    try:
        # Convert data to appropriate format
        if isinstance(data, pd.DataFrame):
            json_data = data.to_dict('records')
        elif isinstance(data, dict):
            json_data = data
        else:
            json_data = data
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.json"
        
        # Add metadata if requested
        if include_metadata:
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_records': len(json_data) if isinstance(json_data, list) else 1,
                    'export_format': 'JSON'
                },
                'data': json_data
            }
        else:
            export_data = json_data
        
        # Create JSON content
        json_content = json.dumps(
            export_data,
            indent=2 if pretty_print else None,
            ensure_ascii=False,
            default=str
        )
        
        # Encode for web display
        json_bytes = json_content.encode('utf-8')
        json_base64 = base64.b64encode(json_bytes).decode()
        
        result = {
            'success': True,
            'filename': filename,
            'format': 'JSON',
            'size_bytes': len(json_bytes),
            'records_count': len(json_data) if isinstance(json_data, list) else 1,
            'download_url': f"data:application/json;base64,{json_base64}",
            'content': json_content
        }
        
        logger.info(f"Successfully exported data to JSON: {filename}")
        return result
        
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        return {
            'success': False,
            'error': str(e),
            'format': 'JSON'
        }


def export_waste_records(
    start_date: date,
    end_date: date,
    export_format: str = 'csv',
    include_predictions: bool = False
) -> Dict[str, Any]:
    """
    Export waste records for a specific date range.
    
    Args:
        start_date: Start date
        end_date: End date
        export_format: Export format ('csv', 'excel', 'json', 'pdf')
        include_predictions: Whether to include prediction data
        
    Returns:
        dict: Export result
    """
    try:
        logger.info(f"Exporting waste records from {start_date} to {end_date}")
        
        # Get waste data
        from .generators import get_waste_data_for_period
        waste_data = get_waste_data_for_period(start_date, end_date)
        
        if waste_data.empty:
            return {
                'success': False,
                'error': 'No waste data found for the specified period'
            }
        
        # Add predictions if requested
        if include_predictions:
            waste_data = add_prediction_data(waste_data)
        
        # Export in requested format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"waste_records_{timestamp}"
        
        if export_format == 'csv':
            return export_to_csv(waste_data, f"{filename}.csv")
        elif export_format == 'excel':
            return export_to_excel(waste_data, f"{filename}.xlsx")
        elif export_format == 'json':
            return export_to_json(waste_data, f"{filename}.json")
        elif export_format == 'pdf':
            return export_to_pdf(waste_data, f"{filename}.pdf", "Waste Records Report")
        else:
            return {
                'success': False,
                'error': f'Unsupported export format: {export_format}'
            }
        
    except Exception as e:
        logger.error(f"Error exporting waste records: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def export_summary_report(
    days_back: int = 30,
    export_format: str = 'pdf'
) -> Dict[str, Any]:
    """
    Export summary report.
    
    Args:
        days_back: Number of days to include
        export_format: Export format
        
    Returns:
        dict: Export result
    """
    try:
        logger.info(f"Exporting summary report for last {days_back} days")
        
        # Generate summary report
        from .generators import generate_summary_report
        report = generate_summary_report(days_back, 'dict')
        
        if 'error' in report:
            return {
                'success': False,
                'error': report.get('error', 'Failed to generate report')
            }
        
        # Export in requested format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_report_{timestamp}"
        
        if export_format == 'pdf':
            return export_to_pdf(report, f"{filename}.pdf", "Summary Report")
        elif export_format == 'excel':
            return export_to_excel(report, f"{filename}.xlsx", "Summary")
        elif export_format == 'json':
            return export_to_json(report, f"{filename}.json")
        else:
            return {
                'success': False,
                'error': f'Unsupported export format for summary: {export_format}'
            }
        
    except Exception as e:
        logger.error(f"Error exporting summary report: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def export_forecast_data(
    days_ahead: int = 7,
    model_type: str = 'xgboost',
    export_format: str = 'csv'
) -> Dict[str, Any]:
    """
    Export forecast data.
    
    Args:
        days_ahead: Number of days to forecast
        model_type: Model type used
        export_format: Export format
        
    Returns:
        dict: Export result
    """
    try:
        logger.info(f"Exporting forecast data for {days_ahead} days using {model_type}")
        
        # Get forecast data
        from .generators import get_forecast_data
        forecast_data = get_forecast_data(days_ahead, model_type)
        
        if not forecast_data:
            return {
                'success': False,
                'error': 'No forecast data available'
            }
        
        # Export in requested format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"forecast_{model_type}_{timestamp}"
        
        if export_format == 'csv':
            return export_to_csv(forecast_data, f"{filename}.csv")
        elif export_format == 'excel':
            return export_to_excel(forecast_data, f"{filename}.xlsx")
        elif export_format == 'json':
            return export_to_json(forecast_data, f"{filename}.json")
        else:
            return {
                'success': False,
                'error': f'Unsupported export format for forecast: {export_format}'
            }
        
    except Exception as e:
        logger.error(f"Error exporting forecast data: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def create_export_package(
    export_types: List[str],
    start_date: date = None,
    end_date: date = None,
    days_back: int = 30
) -> Dict[str, Any]:
    """
    Create a package of multiple exports.
    
    Args:
        export_types: List of export types
        start_date: Start date (optional)
        end_date: End date (optional)
        days_back: Days back if no dates provided
        
    Returns:
        dict: Package export result
    """
    try:
        logger.info(f"Creating export package with types: {export_types}")
        
        # Set date range
        if not start_date or not end_date:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
        
        package_results = {}
        
        # Generate each requested export
        for export_type in export_types:
            if export_type == 'waste_records':
                result = export_waste_records(start_date, end_date, 'csv')
            elif export_type == 'summary_report':
                result = export_summary_report(days_back, 'pdf')
            elif export_type == 'forecast':
                result = export_forecast_data(7, 'xgboost', 'csv')
            elif export_type == 'cost_analysis':
                from .generators import generate_cost_report
                report = generate_cost_report(start_date, end_date, 'dict')
                result = export_to_excel(report, f"cost_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            else:
                result = {'success': False, 'error': f'Unknown export type: {export_type}'}
            
            package_results[export_type] = result
        
        # Count successful exports
        successful_exports = sum(1 for result in package_results.values() if result.get('success', False))
        
        package_result = {
            'success': successful_exports > 0,
            'package_created_at': datetime.now(),
            'export_types_requested': export_types,
            'successful_exports': successful_exports,
            'total_exports': len(export_types),
            'date_range': f"{start_date} to {end_date}",
            'exports': package_results
        }
        
        logger.info(f"Export package created: {successful_exports}/{len(export_types)} successful")
        return package_result
        
    except Exception as e:
        logger.error(f"Error creating export package: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Helper functions

def create_simple_pdf(df: pd.DataFrame, title: str, include_metadata: bool) -> bytes:
    """Create a simple PDF (placeholder implementation)."""
    try:
        # This is a simplified PDF creation
        # In a real implementation, you'd use reportlab or similar
        
        # Create HTML content first
        html_content = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2E8B57; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Generated: {datetime.now()}</p>
            <p>Records: {len(df)}</p>
            <table>
                <tr>
        """
        
        # Add headers
        for col in df.columns:
            html_content += f"<th>{col}</th>"
        
        html_content += "</tr>"
        
        # Add data rows (first 100 to avoid large files)
        for _, row in df.head(100).iterrows():
            html_content += "<tr>"
            for col in df.columns:
                html_content += f"<td>{row[col]}</td>"
            html_content += "</tr>"
        
        html_content += """
            </table>
        </body>
        </html>
        """
        
        # Convert HTML to bytes (simplified)
        pdf_content = html_content.encode('utf-8')
        
        return pdf_content
        
    except Exception as e:
        logger.error(f"Error creating PDF: {e}")
        return b"Error creating PDF"


def add_prediction_data(waste_data: pd.DataFrame) -> pd.DataFrame:
    """Add prediction data to waste data."""
    try:
        # This would integrate with the forecasting module
        # For now, add placeholder predictions
        
        # Add prediction columns
        waste_data['predicted_waste'] = np.random.normal(waste_data['quantity_kg'].mean(), 5, len(waste_data))
        waste_data['prediction_confidence'] = np.random.uniform(0.7, 0.9, len(waste_data))
        
        return waste_data
        
    except Exception as e:
        logger.error(f"Error adding prediction data: {e}")
        return waste_data


def validate_export_data(data: Union[pd.DataFrame, List[Dict], Dict]) -> Dict[str, Any]:
    """Validate data for export."""
    try:
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check if data is empty
        if isinstance(data, pd.DataFrame):
            if data.empty:
                validation_result['issues'].append("DataFrame is empty")
                validation_result['valid'] = False
        elif isinstance(data, list):
            if len(data) == 0:
                validation_result['issues'].append("Data list is empty")
                validation_result['valid'] = False
        elif isinstance(data, dict):
            if not data:
                validation_result['issues'].append("Data dictionary is empty")
                validation_result['valid'] = False
        
        # Check data size
        if isinstance(data, pd.DataFrame):
            if len(data) > 100000:
                validation_result['warnings'].append("Large dataset may take time to export")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating export data: {e}")
        return {
            'valid': False,
            'issues': [str(e)],
            'warnings': []
        }


def get_supported_formats() -> Dict[str, List[str]]:
    """Get supported export formats for different data types."""
    return {
        'tabular': ['csv', 'excel', 'json'],
        'reports': ['pdf', 'excel', 'json'],
        'forecasts': ['csv', 'excel', 'json'],
        'all': ['csv', 'excel', 'json', 'pdf']
    }
