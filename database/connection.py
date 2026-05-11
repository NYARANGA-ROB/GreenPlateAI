"""
Database connection and session management for GreenPlateAI.

This module handles database connections, session management,
and initialization of the database schema.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Global variables for database components
engine = None
SessionLocal = None


def create_database_engine() -> None:
    """Create and configure the database engine."""
    global engine, SessionLocal
    
    config = get_config()
    database_url = config.database_url
    
    # SQLite-specific configuration
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 20
            },
            poolclass=StaticPool,
            echo=config.database_echo,
            pool_pre_ping=True
        )
        
        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
            
    else:
        # PostgreSQL/MySQL configuration
        engine = create_engine(
            database_url,
            echo=config.database_echo,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
    
    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
    
    logger.info(f"Database engine created for: {database_url}")


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.
    
    Yields:
        Session: Database session for use in dependency injection
        
    Raises:
        Exception: If database is not initialized
    """
    if SessionLocal is None:
        raise Exception("Database not initialized. Call init_db() first.")
    
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database.
    
    Creates the database engine, tables, and performs initial setup.
    Should be called once during application startup.
    """
    try:
        # Create engine if not exists
        if engine is None:
            create_database_engine()
        
        # Import all models to ensure they are registered with Base
        from models import user, food_item, waste_record, prediction
        
        # Create all tables
        create_tables()
        
        # Create initial data if needed
        create_initial_data()
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def create_tables() -> None:
    """Create all database tables."""
    if engine is None:
        raise Exception("Database engine not initialized")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def create_initial_data() -> None:
    """Create initial data for the application."""
    if SessionLocal is None:
        raise Exception("Database session factory not initialized")
    
    db = SessionLocal()
    try:
        from models.user import User, UserRole
        from utils.helpers import hash_password
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@greenplateai.com").first()
        if not admin_user:
            # Create default admin user
            admin_user = User(
                email="admin@greenplateai.com",
                username="admin",
                password_hash=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
                full_name="System Administrator"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Default admin user created")
        
        # Create other initial data as needed
        from models.food_item import FoodCategory
        
        # Check if categories exist
        categories = db.query(FoodCategory).count()
        if categories == 0:
            # Create default food categories
            default_categories = [
                FoodCategory(name="Proteins", description="Meat, fish, eggs, legumes"),
                FoodCategory(name="Carbohydrates", description="Rice, pasta, bread, potatoes"),
                FoodCategory(name="Vegetables", description="Fresh and cooked vegetables"),
                FoodCategory(name="Fruits", description="Fresh fruits and fruit salads"),
                FoodCategory(name="Dairy", description="Milk, cheese, yogurt"),
                FoodCategory(name="Beverages", description="Juices, water, soft drinks"),
                FoodCategory(name="Desserts", description="Cakes, pastries, ice cream"),
                FoodCategory(name="Snacks", description="Chips, nuts, granola bars")
            ]
            
            for category in default_categories:
                db.add(category)
            
            db.commit()
            logger.info("Default food categories created")
            
    except Exception as e:
        logger.error(f"Failed to create initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: New database session
        
    Raises:
        Exception: If database is not initialized
    """
    if SessionLocal is None:
        raise Exception("Database not initialized. Call init_db() first.")
    
    return SessionLocal()


def close_db() -> None:
    """Close the database engine and clean up resources."""
    global engine, SessionLocal
    
    if engine:
        engine.dispose()
        engine = None
        SessionLocal = None
        logger.info("Database connection closed")


def check_database_health() -> dict:
    """
    Check database health and connectivity.
    
    Returns:
        dict: Health check results
    """
    try:
        if engine is None:
            return {
                "status": "unhealthy",
                "error": "Database engine not initialized"
            }
        
        # Test database connection
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database_url": str(engine.url).replace(engine.url.password or "", "***"),
            "pool_size": engine.pool.size() if hasattr(engine, 'pool') else None
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Database context manager for transactions
class DatabaseTransaction:
    """Context manager for database transactions."""
    
    def __init__(self, session: Session = None):
        self.session = session or get_session()
        self.should_close = session is None
    
    def __enter__(self) -> Session:
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        except Exception as e:
            logger.error(f"Transaction error: {e}")
            self.session.rollback()
            raise
        finally:
            if self.should_close:
                self.session.close()
