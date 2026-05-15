"""
Report templates and formatting utilities for GreenPlateAI.
This module provides templates for different report types and
functions for formatting and styling report data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


def get_report_template(report_type: str) -> Dict[str, Any]:
    """
    Get report template for specified type.
    
    Args:
        report_type: Type of report
        
    Returns:
        dict: Report template structure
    """
    try:
        templates = {
            'waste_analysis': {
                'title': 'Waste Analysis Report',
                'sections': [
                    'executive_summary',
                    'waste_overview',
                    'category_breakdown',
                    'temporal_analysis',
                    'recommendations'
                ],
                'formatting': {
                    'header_color': '#2E8B57',
                    'accent_color': '#FF6B6B',
                    'font_family': 'Arial',
                    'font_size': 12
                }
            },
            'cost_analysis': {
                'title': 'Cost Analysis Report',
                'sections': [
                    'cost_summary',
                    'cost_by_category',
                    'cost_trends',
                    'efficiency_metrics',
                    'savings_opportunities'
                ],
                'formatting': {
                    'header_color': '#2E8B57',
                    'accent_color': '#4ECDC4',
                    'font_family': 'Arial',
                    'font_size': 12
                }
            },
            'efficiency_report': {
                'title': 'Efficiency Analysis Report',
                'sections': [
                    'efficiency_overview',
                    'performance_metrics',
                    'benchmarking',
                    'improvement_areas',
                    'action_plan'
                ],
                'formatting': {
                    'header_color': '#2E8B57',
                    'accent_color': '#45B7D1',
                    'font_family': 'Arial',
                    'font_size': 12
                }
            },
            'forecast_report': {
                'title': 'Forecast Report',
                'sections': [
                    'forecast_summary',
                    'confidence_analysis',
                    'trend_forecast',
                    'recommendations',
                    'methodology'
                ],
                'formatting': {
                    'header_color': '#2E8B57',
                    'accent_color': '#FFA07A',
                    'font_family': 'Arial',
                    'font_size': 12
                }
            },
            'summary_report': {
                'title': 'Executive Summary Report',
                'sections': [
                    'key_metrics',
                    'trend_analysis',
                    'top_insights',
                    'action_items',
                    'appendix'
                ],
                'formatting': {
                    'header_color': '#2E8B57',
                    'accent_color': '#98D8C8',
                    'font_family': 'Arial',
                    'font_size': 12
                }
            }
        }
        
        return templates.get(report_type, templates['summary_report'])
        
    except Exception as e:
        logger.error(f"Error getting report template: {e}")
        return templates['summary_report']


def format_report_data(data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format report data according to template.
    
    Args:
        data: Raw report data
        template: Report template
        
    Returns:
        dict: Formatted report data
    """
    try:
        formatted_report = {
            'title': template.get('title', 'Report'),
            'generated_at': datetime.now(),
            'sections': {}
        }
        
        # Format each section according to template
        for section in template.get('sections', []):
            if section in data:
                formatted_report['sections'][section] = format_section_data(
                    data[section], section, template
                )
        
        # Add metadata
        formatted_report['metadata'] = {
            'report_type': template.get('title', 'Report'),
            'template_used': template.get('title', 'Default'),
            'sections_count': len(formatted_report['sections'])
        }
        
        return formatted_report
        
    except Exception as e:
        logger.error(f"Error formatting report data: {e}")
        return {'error': str(e)}


def format_section_data(section_data: Any, section_name: str, template: Dict[str, Any]) -> Any:
    """
    Format individual section data.
    
    Args:
        section_data: Raw section data
        section_name: Name of the section
        template: Report template
        
    Returns:
        Formatted section data
    """
    try:
        if section_name == 'executive_summary':
            return format_executive_summary(section_data)
        elif section_name == 'waste_overview':
            return format_waste_overview(section_data)
        elif section_name == 'category_breakdown':
            return format_category_breakdown(section_data)
        elif section_name == 'cost_summary':
            return format_cost_summary(section_data)
        elif section_name == 'key_metrics':
            return format_key_metrics(section_data)
        elif section_name == 'recommendations':
            return format_recommendations(section_data)
        else:
            return section_data  # Return as-is if no specific formatting needed
            
    except Exception as e:
        logger.error(f"Error formatting section {section_name}: {e}")
        return section_data


def apply_report_styling(report_data: Dict[str, Any], output_format: str = 'html') -> str:
    """
    Apply styling to report data.
    
    Args:
        report_data: Formatted report data
        output_format: Output format ('html', 'markdown', 'text')
        
    Returns:
        Styled report content
    """
    try:
        if output_format == 'html':
            return apply_html_styling(report_data)
        elif output_format == 'markdown':
            return apply_markdown_styling(report_data)
        elif output_format == 'text':
            return apply_text_styling(report_data)
        else:
            return str(report_data)
            
    except Exception as e:
        logger.error(f"Error applying report styling: {e}")
        return str(report_data)


# Section formatting functions

def format_executive_summary(data: Any) -> Dict[str, Any]:
    """Format executive summary section."""
    try:
        if isinstance(data, dict):
            return {
                'title': 'Executive Summary',
                'content': data,
                'highlights': extract_key_highlights(data),
                'key_findings': extract_key_findings(data)
            }
        else:
            return {
                'title': 'Executive Summary',
                'content': str(data),
                'highlights': [],
                'key_findings': []
            }
    except Exception as e:
        logger.error(f"Error formatting executive summary: {e}")
        return {'title': 'Executive Summary', 'content': str(data)}


def format_waste_overview(data: Any) -> Dict[str, Any]:
    """Format waste overview section."""
    try:
        if isinstance(data, dict):
            return {
                'title': 'Waste Overview',
                'metrics': data,
                'visualizations': generate_waste_visualizations(data),
                'insights': generate_waste_insights(data)
            }
        else:
            return {
                'title': 'Waste Overview',
                'content': str(data),
                'metrics': {},
                'visualizations': [],
                'insights': []
            }
    except Exception as e:
        logger.error(f"Error formatting waste overview: {e}")
        return {'title': 'Waste Overview', 'content': str(data)}


def format_category_breakdown(data: Any) -> Dict[str, Any]:
    """Format category breakdown section."""
    try:
        if isinstance(data, dict):
            return {
                'title': 'Category Breakdown',
                'categories': data,
                'chart_data': prepare_category_chart_data(data),
                'analysis': analyze_category_data(data)
            }
        else:
            return {
                'title': 'Category Breakdown',
                'content': str(data),
                'categories': {},
                'chart_data': {},
                'analysis': {}
            }
    except Exception as e:
        logger.error(f"Error formatting category breakdown: {e}")
        return {'title': 'Category Breakdown', 'content': str(data)}


def format_cost_summary(data: Any) -> Dict[str, Any]:
    """Format cost summary section."""
    try:
        if isinstance(data, dict):
            return {
                'title': 'Cost Summary',
                'cost_metrics': data,
                'cost_breakdown': analyze_cost_breakdown(data),
                'savings_potential': calculate_savings_potential(data)
            }
        else:
            return {
                'title': 'Cost Summary',
                'content': str(data),
                'cost_metrics': {},
                'cost_breakdown': {},
                'savings_potential': {}
            }
    except Exception as e:
        logger.error(f"Error formatting cost summary: {e}")
        return {'title': 'Cost Summary', 'content': str(data)}


def format_key_metrics(data: Any) -> Dict[str, Any]:
    """Format key metrics section."""
    try:
        if isinstance(data, dict):
            return {
                'title': 'Key Metrics',
                'metrics': data,
                'performance_indicators': extract_performance_indicators(data),
                'trends': identify_metric_trends(data)
            }
        else:
            return {
                'title': 'Key Metrics',
                'content': str(data),
                'metrics': {},
                'performance_indicators': [],
                'trends': {}
            }
    except Exception as e:
        logger.error(f"Error formatting key metrics: {e}")
        return {'title': 'Key Metrics', 'content': str(data)}


def format_recommendations(data: Any) -> Dict[str, Any]:
    """Format recommendations section."""
    try:
        if isinstance(data, list):
            return {
                'title': 'Recommendations',
                'recommendations': data,
                'priority_groups': group_by_priority(data),
                'implementation_plan': create_implementation_plan(data)
            }
        elif isinstance(data, dict):
            return {
                'title': 'Recommendations',
                'recommendations': data,
                'priority_groups': group_by_priority(list(data.values()) if isinstance(data, dict) else data),
                'implementation_plan': create_implementation_plan(data)
            }
        else:
            return {
                'title': 'Recommendations',
                'content': str(data),
                'recommendations': [],
                'priority_groups': {},
                'implementation_plan': {}
            }
    except Exception as e:
        logger.error(f"Error formatting recommendations: {e}")
        return {'title': 'Recommendations', 'content': str(data)}


# Styling functions

def apply_html_styling(report_data: Dict[str, Any]) -> str:
    """Apply HTML styling to report."""
    try:
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{report_data.get('title', 'Report')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    color: #333;
                    line-height: 1.6;
                }}
                .header {{
                    color: #2E8B57;
                    border-bottom: 2px solid #2E8B57;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }}
                .section {{
                    margin-bottom: 30px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .section-title {{
                    color: #FF6B6B;
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 15px;
                }}
                .metric {{
                    display: inline-block;
                    margin: 10px;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 3px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 10px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
                .highlight {{
                    background-color: #e8f5e8;
                    padding: 15px;
                    border-left: 4px solid #2E8B57;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{report_data.get('title', 'Report')}</h1>
                <p>Generated: {report_data.get('generated_at', datetime.now())}</p>
            </div>
        """
        
        # Add sections
        for section_name, section_data in report_data.get('sections', {}).items():
            html += f"""
            <div class="section">
                <div class="section-title">{section_data.get('title', section_name.title())}</div>
                {format_section_html(section_data)}
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        logger.error(f"Error applying HTML styling: {e}")
        return f"<html><body><h1>Error generating report</h1><p>{str(e)}</p></body></html>"


def apply_markdown_styling(report_data: Dict[str, Any]) -> str:
    """Apply Markdown styling to report."""
    try:
        markdown = f"# {report_data.get('title', 'Report')}\n\n"
        markdown += f"*Generated: {report_data.get('generated_at', datetime.now())}*\n\n"
        
        # Add sections
        for section_name, section_data in report_data.get('sections', {}).items():
            markdown += f"## {section_data.get('title', section_name.title())}\n\n"
            markdown += format_section_markdown(section_data)
            markdown += "\n---\n\n"
        
        return markdown
        
    except Exception as e:
        logger.error(f"Error applying Markdown styling: {e}")
        return f"# Error\n\n{str(e)}"


def apply_text_styling(report_data: Dict[str, Any]) -> str:
    """Apply text styling to report."""
    try:
        text = f"{report_data.get('title', 'Report')}\n"
        text += "=" * len(report_data.get('title', 'Report')) + "\n\n"
        text += f"Generated: {report_data.get('generated_at', datetime.now())}\n\n"
        
        # Add sections
        for section_name, section_data in report_data.get('sections', {}).items():
            text += f"{section_data.get('title', section_name.title())}\n"
            text += "-" * len(section_data.get('title', section_name.title())) + "\n\n"
            text += format_section_text(section_data)
            text += "\n\n"
        
        return text
        
    except Exception as e:
        logger.error(f"Error applying text styling: {e}")
        return f"Error\n\n{str(e)}"


# Helper functions

def format_section_html(section_data: Any) -> str:
    """Format section data as HTML."""
    try:
        if isinstance(section_data, dict):
            html = ""
            
            # Add metrics if present
            if 'metrics' in section_data:
                html += "<div class='metrics'>"
                for key, value in section_data['metrics'].items():
                    html += f"<div class='metric'><strong>{key}:</strong> {value}</div>"
                html += "</div>"
            
            # Add content if present
            if 'content' in section_data:
                html += f"<div class='content'>{section_data['content']}</div>"
            
            # Add recommendations if present
            if 'recommendations' in section_data:
                html += "<div class='recommendations'>"
                for rec in section_data['recommendations']:
                    html += f"<div class='highlight'>{rec}</div>"
                html += "</div>"
            
            return html
        else:
            return f"<div class='content'>{str(section_data)}</div>"
            
    except Exception as e:
        logger.error(f"Error formatting section HTML: {e}")
        return f"<div>Error: {str(e)}</div>"


def format_section_markdown(section_data: Any) -> str:
    """Format section data as Markdown."""
    try:
        if isinstance(section_data, dict):
            markdown = ""
            
            # Add metrics if present
            if 'metrics' in section_data:
                for key, value in section_data['metrics'].items():
                    markdown += f"- **{key}:** {value}\n"
                markdown += "\n"
            
            # Add content if present
            if 'content' in section_data:
                markdown += f"{section_data['content']}\n\n"
            
            # Add recommendations if present
            if 'recommendations' in section_data:
                for rec in section_data['recommendations']:
                    markdown += f"- {rec}\n"
                markdown += "\n"
            
            return markdown
        else:
            return f"{str(section_data)}\n\n"
            
    except Exception as e:
        logger.error(f"Error formatting section Markdown: {e}")
        return f"Error: {str(e)}\n\n"


def format_section_text(section_data: Any) -> str:
    """Format section data as plain text."""
    try:
        if isinstance(section_data, dict):
            text = ""
            
            # Add metrics if present
            if 'metrics' in section_data:
                for key, value in section_data['metrics'].items():
                    text += f"{key}: {value}\n"
                text += "\n"
            
            # Add content if present
            if 'content' in section_data:
                text += f"{section_data['content']}\n\n"
            
            # Add recommendations if present
            if 'recommendations' in section_data:
                for rec in section_data['recommendations']:
                    text += f"- {rec}\n"
                text += "\n"
            
            return text
        else:
            return f"{str(section_data)}\n\n"
            
    except Exception as e:
        logger.error(f"Error formatting section text: {e}")
        return f"Error: {str(e)}\n\n"


# Data analysis helpers

def extract_key_highlights(data: Dict[str, Any]) -> List[str]:
    """Extract key highlights from data."""
    try:
        highlights = []
        
        # Look for significant numbers or percentages
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if value > 1000:
                    highlights.append(f"{key}: {value:,}")
                elif isinstance(value, float) and 0 < value < 1:
                    highlights.append(f"{key}: {value:.1%}")
        
        return highlights[:3]  # Return top 3 highlights
        
    except Exception as e:
        logger.error(f"Error extracting highlights: {e}")
        return []


def extract_key_findings(data: Dict[str, Any]) -> List[str]:
    """Extract key findings from data."""
    try:
        findings = []
        
        # Look for trends or patterns
        if 'trend' in data:
            findings.append(f"Overall trend: {data['trend']}")
        
        if 'efficiency_score' in data:
            score = data['efficiency_score']
            if score > 80:
                findings.append("High efficiency performance")
            elif score < 50:
                findings.append("Low efficiency - improvement needed")
        
        return findings
        
    except Exception as e:
        logger.error(f"Error extracting findings: {e}")
        return []


def generate_waste_visualizations(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate visualization specifications for waste data."""
    try:
        visualizations = []
        
        if 'total_waste_kg' in data:
            visualizations.append({
                'type': 'gauge',
                'title': 'Total Waste',
                'value': data['total_waste_kg'],
                'unit': 'kg'
            })
        
        return visualizations
        
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")
        return []


def generate_waste_insights(data: Dict[str, Any]) -> List[str]:
    """Generate insights from waste data."""
    try:
        insights = []
        
        if 'total_waste_kg' in data and data['total_waste_kg'] > 1000:
            insights.append("High waste volume detected")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return []


def prepare_category_chart_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare data for category charts."""
    try:
        chart_data = {}
        
        for category, stats in data.items():
            if isinstance(stats, dict) and 'total_kg' in stats:
                chart_data[category] = stats['total_kg']
        
        return chart_data
        
    except Exception as e:
        logger.error(f"Error preparing chart data: {e}")
        return {}


def analyze_category_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze category breakdown data."""
    try:
        analysis = {
            'top_category': None,
            'total_categories': len(data),
            'distribution': 'even'
        }
        
        if data:
            # Find top category
            top_category = max(data.items(), key=lambda x: x[1].get('total_kg', 0))
            analysis['top_category'] = top_category[0]
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing category data: {e}")
        return {}


def analyze_cost_breakdown(data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze cost breakdown."""
    try:
        return {
            'highest_cost_category': max(data.items(), key=lambda x: x[1]) if data else None,
            'cost_distribution': 'analyzed'
        }
    except Exception as e:
        logger.error(f"Error analyzing cost breakdown: {e}")
        return {}


def calculate_savings_potential(data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate potential savings."""
    try:
        if 'total_cost' in data:
            potential_savings = data['total_cost'] * 0.2  # 20% potential
            return {
                'potential_savings': potential_savings,
                'savings_percentage': 20
            }
        return {}
    except Exception as e:
        logger.error(f"Error calculating savings potential: {e}")
        return {}


def extract_performance_indicators(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract performance indicators."""
    try:
        indicators = []
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                indicators.append({
                    'name': key,
                    'value': value,
                    'unit': 'kg' if 'kg' in key.lower() else 'count'
                })
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error extracting performance indicators: {e}")
        return []


def identify_metric_trends(data: Dict[str, Any]) -> Dict[str, Any]:
    """Identify trends in metrics."""
    try:
        trends = {}
        
        # Simple trend identification
        for key, value in data.items():
            if isinstance(value, (int, float)):
                if value > 100:
                    trends[key] = 'high'
                elif value < 10:
                    trends[key] = 'low'
                else:
                    trends[key] = 'moderate'
        
        return trends
        
    except Exception as e:
        logger.error(f"Error identifying trends: {e}")
        return {}


def group_by_priority(recommendations: List[Any]) -> Dict[str, List[Any]]:
    """Group recommendations by priority."""
    try:
        groups = {
            'high': [],
            'medium': [],
            'low': []
        }
        
        for rec in recommendations:
            if isinstance(rec, dict):
                priority = rec.get('priority', 'medium').lower()
                groups[priority].append(rec)
            else:
                groups['medium'].append(rec)
        
        return groups
        
    except Exception as e:
        logger.error(f"Error grouping by priority: {e}")
        return {'high': [], 'medium': [], 'low': []}


def create_implementation_plan(recommendations: Any) -> Dict[str, Any]:
    """Create implementation plan."""
    try:
        return {
            'timeline': '4-6 weeks',
            'phases': ['planning', 'implementation', 'monitoring'],
            'resources': ['staff', 'training', 'equipment'],
            'success_metrics': ['waste_reduction', 'cost_savings']
        }
    except Exception as e:
        logger.error(f"Error creating implementation plan: {e}")
        return {}
