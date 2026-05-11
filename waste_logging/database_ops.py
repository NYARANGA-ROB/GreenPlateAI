"""
Database operations for Food Waste Logging module.

This module provides database operations for meal preparation,
leftovers, disposed food, serving quantities, and daily reports.
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from database.models import (
    FoodWasteLog, MealLog, User, SustainabilityMetric,
    WasteCategory, MealType
)

logger = logging.getLogger(__name__)


class WasteLoggingDB:
    """Database operations for waste logging."""
    
    def __init__(self, session: Session):
        """Initialize with database session."""
        self.session = session
    
    # Meal Preparation Logging
    def log_meal_preparation(
        self,
        user_id: int,
        dining_hall: str,
        meal_type: MealType,
        food_items: List[Dict[str, Any]],
        preparation_date: date = None
    ) -> Tuple[bool, str, Optional[FoodWasteLog]]:
        """Log meal preparation data."""
        try:
            if not preparation_date:
                preparation_date = date.today()
            
            # Create meal log first
            meal_log = MealLog(
                user_id=user_id,
                meal_type=meal_type,
                dining_hall=dining_hall,
                meal_date=preparation_date,
                meal_time=datetime.utcnow(),
                meal_items=food_items
            )
            
            self.session.add(meal_log)
            self.session.flush()  # Get the ID
            
            # Create waste log for preparation tracking
            waste_log = FoodWasteLog(
                food_item="Meal Preparation",
                category="Prepared Meals",
                waste_category=WasteCategory.PREPARATION,
                quantity_kg=0,  # Will be updated with actual waste
                dining_hall=dining_hall,
                meal_period=meal_type,
                waste_date=preparation_date,
                waste_time=datetime.utcnow(),
                recorded_by=f"User_{user_id}",
                preparation_method="Standard"
            )
            
            self.session.add(waste_log)
            self.session.commit()
            
            logger.info(f"Meal preparation logged for {dining_hall} - {meal_type}")
            return True, "Meal preparation logged successfully", waste_log
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    # Leftovers Logging
    def log_leftovers(
        self,
        user_id: int,
        dining_hall: str,
        meal_type: MealType,
        food_item: str,
        category: str,
        quantity_kg: float,
        estimated_cost: float = None,
        storage_conditions: str = None,
        leftovers_date: date = None
    ) -> Tuple[bool, str, Optional[FoodWasteLog]]:
        """Log leftover food data."""
        try:
            if not leftovers_date:
                leftovers_date = date.today()
            
            # Validate data
            if quantity_kg <= 0:
                return False, "Quantity must be greater than 0", None
            
            waste_log = FoodWasteLog(
                food_item=food_item,
                category=category,
                waste_category=WasteCategory.OVERPRODUCTION,
                quantity_kg=quantity_kg,
                estimated_cost=estimated_cost,
                dining_hall=dining_hall,
                meal_period=meal_type,
                waste_date=leftovers_date,
                waste_time=datetime.utcnow(),
                reason="Leftover from meal service",
                storage_conditions=storage_conditions,
                recorded_by=f"User_{user_id}"
            )
            
            self.session.add(waste_log)
            self.session.commit()
            
            logger.info(f"Leftovers logged: {quantity_kg}kg of {food_item}")
            return True, "Leftovers logged successfully", waste_log
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    # Disposed Food Logging
    def log_disposed_food(
        self,
        user_id: int,
        dining_hall: str,
        food_item: str,
        category: str,
        waste_category: WasteCategory,
        quantity_kg: float,
        estimated_cost: float = None,
        reason: str = None,
        temperature: float = None,
        disposal_method: str = None,
        disposal_date: date = None
    ) -> Tuple[bool, str, Optional[FoodWasteLog]]:
        """Log disposed food data."""
        try:
            if not disposal_date:
                disposal_date = date.today()
            
            # Validate data
            if quantity_kg <= 0:
                return False, "Quantity must be greater than 0", None
            
            waste_log = FoodWasteLog(
                food_item=food_item,
                category=category,
                waste_category=waste_category,
                quantity_kg=quantity_kg,
                estimated_cost=estimated_cost,
                dining_hall=dining_hall,
                waste_date=disposal_date,
                waste_time=datetime.utcnow(),
                reason=reason,
                temperature=temperature,
                preparation_method=disposal_method,
                recorded_by=f"User_{user_id}"
            )
            
            # Calculate environmental impact
            waste_log.co2_equivalent_kg = self._calculate_co2_impact(category, quantity_kg)
            waste_log.water_footprint_liters = self._calculate_water_footprint(category, quantity_kg)
            
            self.session.add(waste_log)
            self.session.commit()
            
            logger.info(f"Disposed food logged: {quantity_kg}kg of {food_item}")
            return True, "Disposed food logged successfully", waste_log
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    # Serving Quantities Tracking
    def log_serving_quantities(
        self,
        user_id: int,
        dining_hall: str,
        meal_type: MealType,
        servings_data: List[Dict[str, Any]],
        serving_date: date = None
    ) -> Tuple[bool, str]:
        """Log serving quantities data."""
        try:
            if not serving_date:
                serving_date = date.today()
            
            success_count = 0
            
            for serving in servings_data:
                food_item = serving.get('food_item')
                category = serving.get('category')
                servings_prepared = serving.get('servings_prepared', 0)
                servings_served = serving.get('servings_served', 0)
                serving_size_kg = serving.get('serving_size_kg', 0)
                
                if not all([food_item, category, servings_prepared > 0]):
                    continue
                
                # Calculate waste from unserved servings
                unserved_servings = servings_prepared - servings_served
                waste_kg = unserved_servings * serving_size_kg
                
                if waste_kg > 0:
                    waste_log = FoodWasteLog(
                        food_item=food_item,
                        category=category,
                        waste_category=WasteCategory.PLATE_WASTE,
                        quantity_kg=waste_kg,
                        dining_hall=dining_hall,
                        meal_period=meal_type,
                        waste_date=serving_date,
                        waste_time=datetime.utcnow(),
                        reason=f"Unserved servings: {unserved_servings}",
                        recorded_by=f"User_{user_id}"
                    )
                    
                    self.session.add(waste_log)
                    success_count += 1
            
            if success_count > 0:
                self.session.commit()
                logger.info(f"Logged serving quantities for {success_count} items")
                return True, f"Successfully logged {success_count} serving records"
            else:
                return True, "No waste detected in serving quantities"
                
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Daily Report Upload
    def upload_daily_report(
        self,
        user_id: int,
        report_data: Dict[str, Any],
        report_date: date = None
    ) -> Tuple[bool, str]:
        """Upload and process daily waste report."""
        try:
            if not report_date:
                report_date = date.today()
            
            dining_hall = report_data.get('dining_hall')
            waste_entries = report_data.get('waste_entries', [])
            
            if not dining_hall or not waste_entries:
                return False, "Invalid report data: missing dining hall or waste entries"
            
            uploaded_count = 0
            
            for entry in waste_entries:
                food_item = entry.get('food_item')
                category = entry.get('category')
                waste_category_str = entry.get('waste_category', 'other')
                quantity_kg = entry.get('quantity_kg', 0)
                estimated_cost = entry.get('estimated_cost')
                reason = entry.get('reason')
                
                # Convert waste category string to enum
                try:
                    waste_category = WasteCategory(waste_category_str)
                except ValueError:
                    waste_category = WasteCategory.OTHER
                
                if not all([food_item, category, quantity_kg > 0]):
                    continue
                
                waste_log = FoodWasteLog(
                    food_item=food_item,
                    category=category,
                    waste_category=waste_category,
                    quantity_kg=quantity_kg,
                    estimated_cost=estimated_cost,
                    dining_hall=dining_hall,
                    waste_date=report_date,
                    waste_time=datetime.utcnow(),
                    reason=reason,
                    recorded_by=f"User_{user_id}",
                    source_station="Daily Report Upload"
                )
                
                # Calculate environmental impact
                waste_log.co2_equivalent_kg = self._calculate_co2_impact(category, quantity_kg)
                waste_log.water_footprint_liters = self._calculate_water_footprint(category, quantity_kg)
                
                self.session.add(waste_log)
                uploaded_count += 1
            
            if uploaded_count > 0:
                self.session.commit()
                logger.info(f"Daily report uploaded: {uploaded_count} waste entries")
                return True, f"Successfully uploaded {uploaded_count} waste entries"
            else:
                return False, "No valid waste entries found in report"
                
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Query Methods
    def get_waste_logs_by_date_range(
        self,
        start_date: date,
        end_date: date,
        dining_hall: str = None,
        waste_category: WasteCategory = None
    ) -> List[FoodWasteLog]:
        """Get waste logs within date range."""
        try:
            query = self.session.query(FoodWasteLog).filter(
                and_(
                    FoodWasteLog.waste_date >= start_date,
                    FoodWasteLog.waste_date <= end_date,
                    FoodWasteLog.is_active == True
                )
            )
            
            if dining_hall:
                query = query.filter(FoodWasteLog.dining_hall == dining_hall)
            
            if waste_category:
                query = query.filter(FoodWasteLog.waste_category == waste_category)
            
            return query.order_by(desc(FoodWasteLog.waste_date)).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error querying waste logs: {str(e)}")
            return []
    
    def get_waste_summary_by_date(
        self,
        target_date: date,
        dining_hall: str = None
    ) -> Dict[str, Any]:
        """Get waste summary for a specific date."""
        try:
            query = self.session.query(
                func.sum(FoodWasteLog.quantity_kg).label('total_waste'),
                func.sum(FoodWasteLog.estimated_cost).label('total_cost'),
                func.count(FoodWasteLog.id).label('entry_count')
            ).filter(
                and_(
                    FoodWasteLog.waste_date == target_date,
                    FoodWasteLog.is_active == True
                )
            )
            
            if dining_hall:
                query = query.filter(FoodWasteLog.dining_hall == dining_hall)
            
            result = query.first()
            
            return {
                'total_waste_kg': float(result.total_waste or 0),
                'total_cost': float(result.total_cost or 0),
                'entry_count': int(result.entry_count or 0)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting waste summary: {str(e)}")
            return {'total_waste_kg': 0, 'total_cost': 0, 'entry_count': 0}
    
    def get_category_breakdown(
        self,
        start_date: date,
        end_date: date,
        dining_hall: str = None
    ) -> List[Dict[str, Any]]:
        """Get waste breakdown by category."""
        try:
            query = self.session.query(
                FoodWasteLog.category,
                func.sum(FoodWasteLog.quantity_kg).label('total_quantity'),
                func.count(FoodWasteLog.id).label('entry_count')
            ).filter(
                and_(
                    FoodWasteLog.waste_date >= start_date,
                    FoodWasteLog.waste_date <= end_date,
                    FoodWasteLog.is_active == True
                )
            )
            
            if dining_hall:
                query = query.filter(FoodWasteLog.dining_hall == dining_hall)
            
            results = query.group_by(FoodWasteLog.category).all()
            
            return [
                {
                    'category': result.category,
                    'total_quantity': float(result.total_quantity),
                    'entry_count': int(result.entry_count)
                }
                for result in results
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting category breakdown: {str(e)}")
            return []
    
    def get_dining_halls_list(self) -> List[str]:
        """Get list of all dining halls."""
        try:
            result = self.session.query(FoodWasteLog.dining_hall).distinct().all()
            return [row.dining_hall for row in result]
        except SQLAlchemyError as e:
            logger.error(f"Error getting dining halls: {str(e)}")
            return []
    
    # Update and Delete Operations
    def update_waste_log(
        self,
        waste_log_id: int,
        update_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update existing waste log."""
        try:
            waste_log = self.session.query(FoodWasteLog).filter(
                FoodWasteLog.id == waste_log_id,
                FoodWasteLog.is_active == True
            ).first()
            
            if not waste_log:
                return False, "Waste log not found"
            
            # Update allowed fields
            updatable_fields = [
                'quantity_kg', 'estimated_cost', 'reason', 'temperature',
                'storage_conditions', 'food_quality_rating', 'appearance_rating'
            ]
            
            for field, value in update_data.items():
                if field in updatable_fields and hasattr(waste_log, field):
                    setattr(waste_log, field, value)
            
            waste_log.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Waste log {waste_log_id} updated successfully")
            return True, "Waste log updated successfully"
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def delete_waste_log(self, waste_log_id: int) -> Tuple[bool, str]:
        """Soft delete waste log."""
        try:
            waste_log = self.session.query(FoodWasteLog).filter(
                FoodWasteLog.id == waste_log_id,
                FoodWasteLog.is_active == True
            ).first()
            
            if not waste_log:
                return False, "Waste log not found"
            
            waste_log.is_active = False
            waste_log.updated_at = datetime.utcnow()
            self.session.commit()
            
            logger.info(f"Waste log {waste_log_id} deleted successfully")
            return True, "Waste log deleted successfully"
            
        except SQLAlchemyError as e:
            self.session.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            self.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    # Helper Methods
    def _calculate_co2_impact(self, category: str, quantity_kg: float) -> float:
        """Calculate CO2 equivalent impact."""
        # CO2 impact factors by category (kg CO2 per kg of food)
        co2_factors = {
            'Meat': 27.0,
            'Dairy': 13.5,
            'Vegetables': 2.0,
            'Fruits': 1.5,
            'Grains': 2.5,
            'Seafood': 20.0,
            'Processed': 10.0,
            'Other': 5.0
        }
        
        factor = co2_factors.get(category, 5.0)
        return quantity_kg * factor
    
    def _calculate_water_footprint(self, category: str, quantity_kg: float) -> float:
        """Calculate water footprint."""
        # Water footprint factors by category (liters per kg of food)
        water_factors = {
            'Meat': 15000,
            'Dairy': 1000,
            'Vegetables': 300,
            'Fruits': 800,
            'Grains': 1600,
            'Seafood': 5000,
            'Processed': 2000,
            'Other': 1000
        }
        
        factor = water_factors.get(category, 1000)
        return quantity_kg * factor
    
    def get_waste_trends(
        self,
        days: int = 30,
        dining_hall: str = None
    ) -> List[Dict[str, Any]]:
        """Get waste trends over time."""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            query = self.session.query(
                FoodWasteLog.waste_date,
                func.sum(FoodWasteLog.quantity_kg).label('daily_waste'),
                func.count(FoodWasteLog.id).label('entry_count')
            ).filter(
                and_(
                    FoodWasteLog.waste_date >= start_date,
                    FoodWasteLog.waste_date <= end_date,
                    FoodWasteLog.is_active == True
                )
            )
            
            if dining_hall:
                query = query.filter(FoodWasteLog.dining_hall == dining_hall)
            
            results = query.group_by(FoodWasteLog.waste_date).all()
            
            return [
                {
                    'date': result.waste_date.isoformat(),
                    'daily_waste': float(result.daily_waste),
                    'entry_count': int(result.entry_count)
                }
                for result in results
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting waste trends: {str(e)}")
            return []
    
    def get_top_waste_items(
        self,
        days: int = 7,
        limit: int = 10,
        dining_hall: str = None
    ) -> List[Dict[str, Any]]:
        """Get top waste items."""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            query = self.session.query(
                FoodWasteLog.food_item,
                func.sum(FoodWasteLog.quantity_kg).label('total_quantity'),
                func.count(FoodWasteLog.id).label('occurrence_count')
            ).filter(
                and_(
                    FoodWasteLog.waste_date >= start_date,
                    FoodWasteLog.waste_date <= end_date,
                    FoodWasteLog.is_active == True
                )
            )
            
            if dining_hall:
                query = query.filter(FoodWasteLog.dining_hall == dining_hall)
            
            results = query.group_by(FoodWasteLog.food_item).order_by(
                desc(func.sum(FoodWasteLog.quantity_kg))
            ).limit(limit).all()
            
            return [
                {
                    'food_item': result.food_item,
                    'total_quantity': float(result.total_quantity),
                    'occurrence_count': int(result.occurrence_count)
                }
                for result in results
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting top waste items: {str(e)}")
            return []
