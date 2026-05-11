"""
Database initialization and management for GreenPlateAI.

This module provides database setup, initialization, and migration utilities
for production-ready deployment.
"""

import os
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json

from .models import (
    Base, User, MealLog, FoodWasteLog, Feedback, 
    Prediction, Alert, SustainabilityMetric,
    UserRole, MealType, WasteCategory, AlertType, 
    FeedbackType, PredictionStatus, AlertStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database management class for GreenPlateAI."""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager."""
        self.database_url = database_url or os.getenv(
            'DATABASE_URL', 
            'sqlite:///greenplateai.db'
        )
        self.engine = None
        self.SessionLocal = None
        
    def initialize_engine(self):
        """Initialize database engine."""
        try:
            # Create engine with SQLite-specific settings
            if self.database_url.startswith('sqlite'):
                self.engine = create_engine(
                    self.database_url,
                    echo=False,
                    pool_pre_ping=True,
                    connect_args={
                        'check_same_thread': False,
                        'timeout': 20
                    }
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=10,
                    max_overflow=20
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("Database engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables."""
        try:
            if not self.engine:
                self.initialize_engine()
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        try:
            if not self.engine:
                self.initialize_engine()
            
            # Drop all tables
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop database tables: {e}")
            return False
    
    def get_session(self) -> Session:
        """Get database session."""
        if not self.SessionLocal:
            self.initialize_engine()
        
        return self.SessionLocal()
    
    def initialize_database(self, create_sample_data: bool = False):
        """Initialize complete database with optional sample data."""
        try:
            # Initialize engine
            if not self.initialize_engine():
                return False
            
            # Create tables
            if not self.create_tables():
                return False
            
            # Create initial data
            if create_sample_data:
                self.create_initial_data()
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def create_initial_data(self):
        """Create initial data for the database."""
        try:
            session = self.get_session()
            
            # Check if admin user already exists
            existing_admin = session.query(User).filter_by(username="admin").first()
            if not existing_admin:
                # Create admin user
                admin_user = User(
                    email="admin@greenplateai.com",
                    username="admin",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJguxqjIe",  # admin123
                    role=UserRole.ADMIN,
                    full_name="System Administrator",
                    is_verified=True,
                    preferences={"theme": "light", "notifications": True}
                )
                session.add(admin_user)
                logger.info("Created admin user")
            else:
                logger.info("Admin user already exists")
            
            # Check if kitchen staff already exists
            existing_kitchen = session.query(User).filter_by(username="kitchen_staff").first()
            if not existing_kitchen:
                # Create sample kitchen staff
                kitchen_staff = User(
                    email="kitchen@greenplateai.com",
                    username="kitchen_staff",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJguxqjIe",  # kitchen123
                    role=UserRole.KITCHEN_STAFF,
                    full_name="Kitchen Manager",
                    department="Food Services",
                    is_verified=True,
                    preferences={"notifications": True, "reports": "daily"}
                )
                session.add(kitchen_staff)
                logger.info("Created kitchen staff user")
            else:
                logger.info("Kitchen staff user already exists")
            
            # Check if student already exists
            existing_student = session.query(User).filter_by(username="student").first()
            if not existing_student:
                # Create sample student
                student = User(
                    email="student@greenplateai.com",
                    username="student",
                    password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJguxqjIe",  # student123
                    role=UserRole.STUDENT,
                    full_name="Student User",
                    student_id="STU001",
                    is_verified=True,
                    preferences={"theme": "dark", "notifications": False}
                )
                session.add(student)
                logger.info("Created student user")
            else:
                logger.info("Student user already exists")
            
            # Create sample sustainability metrics
            metrics_data = [
                {
                    "metric_name": "total_waste_kg",
                    "metric_type": "waste",
                    "unit": "kg",
                    "metric_date": date.today(),
                    "value": 45.5,
                    "baseline_value": 75.0,
                    "target_value": 30.0,
                    "dining_hall": "Main Hall"
                },
                {
                    "metric_name": "co2_reduction_kg",
                    "metric_type": "environmental",
                    "unit": "kg",
                    "metric_date": date.today(),
                    "value": 125.3,
                    "baseline_value": 100.0,
                    "target_value": 150.0,
                    "dining_hall": "Main Hall"
                },
                {
                    "metric_name": "cost_savings",
                    "metric_type": "cost",
                    "unit": "$",
                    "metric_date": date.today(),
                    "value": 234.50,
                    "baseline_value": 0.0,
                    "target_value": 500.0,
                    "dining_hall": "Main Hall"
                }
            ]
            
            for metric_data in metrics_data:
                metric = SustainabilityMetric(**metric_data)
                metric.calculate_percentage_change()
                metric.calculate_achievement()
                session.add(metric)
            
            # Create sample alerts
            alerts_data = [
                {
                    "alert_type": AlertType.HIGH_WASTE,
                    "title": "High Waste Alert",
                    "message": "Waste levels are 20% above average today",
                    "severity": "medium",
                    "dining_hall": "Main Hall",
                    "source": "system"
                },
                {
                    "alert_type": AlertType.LOW_INVENTORY,
                    "title": "Low Inventory Warning",
                    "message": "Chicken stock is below 20% capacity",
                    "severity": "low",
                    "dining_hall": "Main Hall",
                    "source": "system"
                }
            ]
            
            for alert_data in alerts_data:
                alert = Alert(**alert_data)
                session.add(alert)
            
            session.commit()
            logger.info("Initial data created successfully")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create initial data: {e}")
            raise
        finally:
            session.close()
    
    def backup_database(self, backup_path: str = None):
        """Create database backup."""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_greenplateai_{timestamp}.db"
            
            if self.database_url.startswith('sqlite'):
                import shutil
                db_path = self.database_url.replace('sqlite:///', '')
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                return True
            else:
                # For PostgreSQL/MySQL, use pg_dump or mysqldump
                logger.warning("Backup not implemented for non-SQLite databases")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    def restore_database(self, backup_path: str):
        """Restore database from backup."""
        try:
            if self.database_url.startswith('sqlite'):
                import shutil
                db_path = self.database_url.replace('sqlite:///', '')
                shutil.copy2(backup_path, db_path)
                logger.info(f"Database restored from {backup_path}")
                return True
            else:
                logger.warning("Restore not implemented for non-SQLite databases")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        try:
            session = self.get_session()
            
            # Get table counts
            info = {
                "database_url": self.database_url,
                "tables": {},
                "total_records": 0
            }
            
            tables = [
                ("users", User),
                ("meal_logs", MealLog),
                ("food_waste_logs", FoodWasteLog),
                ("feedback", Feedback),
                ("predictions", Prediction),
                ("alerts", Alert),
                ("sustainability_metrics", SustainabilityMetric)
            ]
            
            for table_name, model in tables:
                count = session.query(model).count()
                info["tables"][table_name] = count
                info["total_records"] += count
            
            session.close()
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}
    
    def cleanup_expired_data(self):
        """Clean up expired data and optimize database."""
        try:
            session = self.get_session()
            
            # Clean up expired alerts
            expired_alerts = session.query(Alert).filter(
                Alert.expires_at < datetime.utcnow(),
                Alert.status == AlertStatus.ACTIVE
            ).all()
            
            for alert in expired_alerts:
                alert.status = AlertStatus.DISMISSED
                alert.resolution_notes = "Auto-dismissed due to expiration"
            
            # Clean up old predictions (older than 1 year)
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            
            old_predictions = session.query(Prediction).filter(
                Prediction.created_at < cutoff_date,
                Prediction.status != PredictionStatus.ARCHIVED
            ).all()
            
            for prediction in old_predictions:
                prediction.status = PredictionStatus.ARCHIVED
            
            session.commit()
            logger.info("Database cleanup completed")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to cleanup database: {e}")
            raise
        finally:
            session.close()


# Migration Management
class MigrationManager:
    """Database migration management."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize migration manager."""
        self.db_manager = db_manager
        self.migrations = {}
    
    def create_migration_table(self):
        """Create migrations tracking table."""
        try:
            session = self.db_manager.get_session()
            
            # Create migration tracking table
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            session.commit()
            logger.info("Migration table created/verified")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create migration table: {e}")
            raise
        finally:
            session.close()
    
    def get_applied_migrations(self) -> list:
        """Get list of applied migrations."""
        try:
            session = self.db_manager.get_session()
            
            result = session.execute(text("SELECT migration_name FROM migrations ORDER BY applied_at"))
            applied = [row[0] for row in result]
            
            session.close()
            return applied
            
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def apply_migration(self, migration_name: str, migration_sql: str):
        """Apply a migration."""
        try:
            session = self.db_manager.get_session()
            
            # Check if migration already applied
            applied = self.get_applied_migrations()
            if migration_name in applied:
                logger.info(f"Migration {migration_name} already applied")
                return True
            
            # Apply migration
            session.execute(text(migration_sql))
            
            # Record migration
            session.execute(text(
                "INSERT INTO migrations (migration_name) VALUES (:name)"
            ), {"name": migration_name})
            
            session.commit()
            logger.info(f"Migration {migration_name} applied successfully")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to apply migration {migration_name}: {e}")
            return False
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()


def init_database(database_url: str = None, create_sample_data: bool = False) -> bool:
    """Initialize the database."""
    global db_manager
    
    if database_url:
        db_manager = DatabaseManager(database_url)
    
    return db_manager.initialize_database(create_sample_data)


def get_db() -> Session:
    """Get database session."""
    return db_manager.get_session()


def create_tables() -> bool:
    """Create database tables."""
    return db_manager.create_tables()


def get_database_info() -> Dict[str, Any]:
    """Get database information."""
    return db_manager.get_database_info()


# Database health check
def health_check() -> Dict[str, Any]:
    """Perform database health check."""
    try:
        session = get_db()
        
        # Test basic query
        session.execute(text("SELECT 1"))
        
        # Get database info
        info = get_database_info()
        
        session.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database_info": info
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


# CLI functions for database management
def cli_init():
    """CLI command to initialize database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize GreenPlateAI database")
    parser.add_argument("--sample-data", action="store_true", help="Create sample data")
    parser.add_argument("--db-url", help="Database URL")
    
    args = parser.parse_args()
    
    success = init_database(args.db_url, args.sample_data)
    
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Failed to initialize database")
        exit(1)


def cli_info():
    """CLI command to show database info."""
    info = get_database_info()
    
    print("📊 Database Information")
    print(f"Database URL: {info.get('database_url', 'Unknown')}")
    print(f"Total Records: {info.get('total_records', 0)}")
    
    if 'tables' in info:
        print("\n📋 Table Counts:")
        for table, count in info['tables'].items():
            print(f"  {table}: {count}")


def cli_backup():
    """CLI command to backup database."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup GreenPlateAI database")
    parser.add_argument("--output", help="Backup file path")
    
    args = parser.parse_args()
    
    success = db_manager.backup_database(args.output)
    
    if success:
        print("✅ Database backed up successfully")
    else:
        print("❌ Failed to backup database")
        exit(1)


if __name__ == "__main__":
    # For direct execution
    cli_init()
