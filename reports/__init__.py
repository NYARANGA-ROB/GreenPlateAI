"""
Reports module for GreenPlateAI.

This module provides report generation, data export,
and analytics reporting capabilities.
"""

from .generators import (
    generate_waste_report,
    generate_cost_report,
    generate_efficiency_report,
    generate_forecast_report,
    generate_summary_report
)
from .exporters import (
    export_to_csv,
    export_to_excel,
    export_to_pdf,
    export_to_json
)
from .templates import (
    get_report_template,
    format_report_data,
    apply_report_styling
)

__all__ = [
    # Generators
    'generate_waste_report',
    'generate_cost_report',
    'generate_efficiency_report',
    'generate_forecast_report',
    'generate_summary_report',
    
    # Exporters
    'export_to_csv',
    'export_to_excel',
    'export_to_pdf',
    'export_to_json',
    
    # Templates
    'get_report_template',
    'format_report_data',
    'apply_report_styling'
]
