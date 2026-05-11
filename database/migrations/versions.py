"""
Migration versions for GreenPlateAI database.

This module contains all migration definitions with up and down SQL
for database schema changes.
"""

import hashlib
from typing import List, Dict, Any


def get_all_migrations() -> List[Dict[str, Any]]:
    """Get all available migrations in order."""
    migrations = [
        {
            "version": "001_initial_schema",
            "description": "Initial database schema creation",
            "checksum": "a1b2c3d4e5f6",
            "up_sql": [
                # Users table
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'student' NOT NULL,
                    full_name VARCHAR(255),
                    phone VARCHAR(20),
                    department VARCHAR(100),
                    student_id VARCHAR(50),
                    employee_id VARCHAR(50),
                    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                    last_login DATETIME,
                    login_count INTEGER DEFAULT 0 NOT NULL,
                    failed_login_attempts INTEGER DEFAULT 0 NOT NULL,
                    locked_until DATETIME,
                    password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    preferences TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL
                )
                """,
                
                # Meal logs table
                """
                CREATE TABLE meal_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    meal_type VARCHAR(50) NOT NULL,
                    dining_hall VARCHAR(100) NOT NULL,
                    meal_items TEXT,
                    calories INTEGER,
                    protein REAL,
                    carbs REAL,
                    fat REAL,
                    fiber REAL,
                    satisfaction_rating INTEGER,
                    portion_size_rating INTEGER,
                    taste_rating INTEGER,
                    notes TEXT,
                    meal_date DATE DEFAULT CURRENT_DATE NOT NULL,
                    meal_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """,
                
                # Food waste logs table
                """
                CREATE TABLE food_waste_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    food_item VARCHAR(255) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    waste_category VARCHAR(50) NOT NULL,
                    quantity_kg REAL NOT NULL,
                    quantity_servings INTEGER,
                    estimated_cost REAL,
                    dining_hall VARCHAR(100) NOT NULL,
                    meal_period VARCHAR(50),
                    source_station VARCHAR(100),
                    waste_date DATE DEFAULT CURRENT_DATE NOT NULL,
                    waste_time DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    reason TEXT,
                    temperature REAL,
                    storage_conditions VARCHAR(255),
                    preparation_method VARCHAR(100),
                    co2_equivalent_kg REAL,
                    water_footprint_liters REAL,
                    land_use_m2 REAL,
                    food_quality_rating INTEGER,
                    appearance_rating INTEGER,
                    recorded_by VARCHAR(255),
                    verified_by VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    CHECK (quantity_kg >= 0),
                    CHECK (estimated_cost >= 0),
                    CHECK (co2_equivalent_kg >= 0),
                    CHECK (water_footprint_liters >= 0),
                    CHECK (land_use_m2 >= 0)
                )
                """,
                
                # Feedback table
                """
                CREATE TABLE feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    feedback_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(100),
                    severity VARCHAR(50),
                    meal_id INTEGER,
                    waste_log_id INTEGER,
                    dining_hall VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'open',
                    priority VARCHAR(50) DEFAULT 'medium',
                    assigned_to VARCHAR(255),
                    resolution TEXT,
                    resolved_at DATETIME,
                    satisfaction_rating INTEGER,
                    response_time_hours REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (meal_id) REFERENCES meal_logs (id),
                    FOREIGN KEY (waste_log_id) REFERENCES food_waste_logs (id)
                )
                """,
                
                # Predictions table
                """
                CREATE TABLE predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_type VARCHAR(100) NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    model_version VARCHAR(50),
                    target_date DATE NOT NULL,
                    target_period VARCHAR(50),
                    confidence_score REAL,
                    predicted_value REAL NOT NULL,
                    predicted_min REAL,
                    predicted_max REAL,
                    dining_hall VARCHAR(100),
                    meal_type VARCHAR(50),
                    food_category VARCHAR(100),
                    actual_value REAL,
                    accuracy_score REAL,
                    error_percentage REAL,
                    model_parameters TEXT,
                    training_data_period VARCHAR(100),
                    features_used TEXT,
                    status VARCHAR(50) DEFAULT 'pending',
                    processing_started_at DATETIME,
                    processing_completed_at DATETIME,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    CHECK (confidence_score >= 0 AND confidence_score <= 1),
                    CHECK (accuracy_score >= 0 AND accuracy_score <= 1)
                )
                """,
                
                # Alerts table
                """
                CREATE TABLE alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type VARCHAR(50) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    severity VARCHAR(50) DEFAULT 'medium',
                    user_id INTEGER,
                    dining_hall VARCHAR(100),
                    target_role VARCHAR(50),
                    prediction_id INTEGER,
                    waste_log_id INTEGER,
                    status VARCHAR(50) DEFAULT 'active',
                    acknowledged_by VARCHAR(255),
                    acknowledged_at DATETIME,
                    resolved_by VARCHAR(255),
                    resolved_at DATETIME,
                    resolution_notes TEXT,
                    expires_at DATETIME,
                    auto_resolve BOOLEAN DEFAULT FALSE,
                    source VARCHAR(100),
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (prediction_id) REFERENCES predictions (id),
                    FOREIGN KEY (waste_log_id) REFERENCES food_waste_logs (id)
                )
                """,
                
                # Sustainability metrics table
                """
                CREATE TABLE sustainability_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name VARCHAR(100) NOT NULL,
                    metric_type VARCHAR(50) NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    metric_date DATE NOT NULL,
                    period_type VARCHAR(20) DEFAULT 'daily',
                    value REAL NOT NULL,
                    baseline_value REAL,
                    target_value REAL,
                    previous_value REAL,
                    dining_hall VARCHAR(100),
                    category VARCHAR(100),
                    meal_type VARCHAR(50),
                    waste_log_id INTEGER,
                    percentage_change REAL,
                    achievement_percentage REAL,
                    calculation_method VARCHAR(255),
                    data_source VARCHAR(100),
                    confidence_level REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    FOREIGN KEY (waste_log_id) REFERENCES food_waste_logs (id),
                    CHECK (confidence_level >= 0 AND confidence_level <= 1)
                )
                """
            ],
            "down_sql": [
                "DROP TABLE IF EXISTS sustainability_metrics",
                "DROP TABLE IF EXISTS alerts",
                "DROP TABLE IF EXISTS predictions",
                "DROP TABLE IF EXISTS feedback",
                "DROP TABLE IF EXISTS food_waste_logs",
                "DROP TABLE IF EXISTS meal_logs",
                "DROP TABLE IF EXISTS users"
            ]
        },
        
        {
            "version": "002_add_indexes",
            "description": "Add performance indexes for frequently queried columns",
            "checksum": "b2c3d4e5f6g7",
            "up_sql": [
                # Users table indexes
                "CREATE INDEX idx_users_email ON users(email)",
                "CREATE INDEX idx_users_username ON users(username)",
                "CREATE INDEX idx_users_role ON users(role)",
                "CREATE INDEX idx_users_active ON users(is_active)",
                "CREATE INDEX idx_users_created_at ON users(created_at)",
                
                # Meal logs indexes
                "CREATE INDEX idx_meal_logs_user_id ON meal_logs(user_id)",
                "CREATE INDEX idx_meal_logs_meal_date ON meal_logs(meal_date)",
                "CREATE INDEX idx_meal_logs_dining_hall ON meal_logs(dining_hall)",
                "CREATE INDEX idx_meal_logs_meal_type ON meal_logs(meal_type)",
                "CREATE INDEX idx_meal_logs_active ON meal_logs(is_active)",
                
                # Food waste logs indexes
                "CREATE INDEX idx_food_waste_logs_category ON food_waste_logs(category)",
                "CREATE INDEX idx_food_waste_logs_waste_category ON food_waste_logs(waste_category)",
                "CREATE INDEX idx_food_waste_logs_dining_hall ON food_waste_logs(dining_hall)",
                "CREATE INDEX idx_food_waste_logs_waste_date ON food_waste_logs(waste_date)",
                "CREATE INDEX idx_food_waste_logs_meal_period ON food_waste_logs(meal_period)",
                "CREATE INDEX idx_food_waste_logs_active ON food_waste_logs(is_active)",
                
                # Feedback indexes
                "CREATE INDEX idx_feedback_user_id ON feedback(user_id)",
                "CREATE INDEX idx_feedback_type ON feedback(feedback_type)",
                "CREATE INDEX idx_feedback_status ON feedback(status)",
                "CREATE INDEX idx_feedback_priority ON feedback(priority)",
                "CREATE INDEX idx_feedback_created_at ON feedback(created_at)",
                "CREATE INDEX idx_feedback_active ON feedback(is_active)",
                
                # Predictions indexes
                "CREATE INDEX idx_predictions_type ON predictions(prediction_type)",
                "CREATE INDEX idx_predictions_target_date ON predictions(target_date)",
                "CREATE INDEX idx_predictions_model_name ON predictions(model_name)",
                "CREATE INDEX idx_predictions_status ON predictions(status)",
                "CREATE INDEX idx_predictions_dining_hall ON predictions(dining_hall)",
                "CREATE INDEX idx_predictions_active ON predictions(is_active)",
                
                # Alerts indexes
                "CREATE INDEX idx_alerts_type ON alerts(alert_type)",
                "CREATE INDEX idx_alerts_status ON alerts(status)",
                "CREATE INDEX idx_alerts_severity ON alerts(severity)",
                "CREATE INDEX idx_alerts_user_id ON alerts(user_id)",
                "CREATE INDEX idx_alerts_dining_hall ON alerts(dining_hall)",
                "CREATE INDEX idx_alerts_expires_at ON alerts(expires_at)",
                "CREATE INDEX idx_alerts_active ON alerts(is_active)",
                
                # Sustainability metrics indexes
                "CREATE INDEX idx_sustainability_metrics_name ON sustainability_metrics(metric_name)",
                "CREATE INDEX idx_sustainability_metrics_type ON sustainability_metrics(metric_type)",
                "CREATE INDEX idx_sustainability_metrics_date ON sustainability_metrics(metric_date)",
                "CREATE INDEX idx_sustainability_metrics_dining_hall ON sustainability_metrics(dining_hall)",
                "CREATE INDEX idx_sustainability_metrics_active ON sustainability_metrics(is_active)"
            ],
            "down_sql": [
                "DROP INDEX IF EXISTS idx_sustainability_metrics_active",
                "DROP INDEX IF EXISTS idx_sustainability_metrics_dining_hall",
                "DROP INDEX IF EXISTS idx_sustainability_metrics_date",
                "DROP INDEX IF EXISTS idx_sustainability_metrics_type",
                "DROP INDEX IF EXISTS idx_sustainability_metrics_name",
                "DROP INDEX IF EXISTS idx_alerts_active",
                "DROP INDEX IF EXISTS idx_alerts_expires_at",
                "DROP INDEX IF EXISTS idx_alerts_dining_hall",
                "DROP INDEX IF EXISTS idx_alerts_user_id",
                "DROP INDEX IF EXISTS idx_alerts_severity",
                "DROP INDEX IF EXISTS idx_alerts_status",
                "DROP INDEX IF EXISTS idx_alerts_type",
                "DROP INDEX IF EXISTS idx_predictions_active",
                "DROP INDEX IF EXISTS idx_predictions_dining_hall",
                "DROP INDEX IF EXISTS idx_predictions_status",
                "DROP INDEX IF EXISTS idx_predictions_model_name",
                "DROP INDEX IF EXISTS idx_predictions_target_date",
                "DROP INDEX IF EXISTS idx_predictions_type",
                "DROP INDEX IF EXISTS idx_feedback_active",
                "DROP INDEX IF EXISTS idx_feedback_created_at",
                "DROP INDEX IF EXISTS idx_feedback_priority",
                "DROP INDEX IF EXISTS idx_feedback_status",
                "DROP INDEX IF EXISTS idx_feedback_type",
                "DROP INDEX IF EXISTS idx_feedback_user_id",
                "DROP INDEX IF EXISTS idx_food_waste_logs_active",
                "DROP INDEX IF EXISTS idx_food_waste_logs_meal_period",
                "DROP INDEX IF EXISTS idx_food_waste_logs_waste_date",
                "DROP INDEX IF EXISTS idx_food_waste_logs_dining_hall",
                "DROP INDEX IF EXISTS idx_food_waste_logs_waste_category",
                "DROP INDEX IF EXISTS idx_food_waste_logs_category",
                "DROP INDEX IF EXISTS idx_meal_logs_active",
                "DROP INDEX IF EXISTS idx_meal_logs_meal_type",
                "DROP INDEX IF EXISTS idx_meal_logs_dining_hall",
                "DROP INDEX IF EXISTS idx_meal_logs_meal_date",
                "DROP INDEX IF EXISTS idx_meal_logs_user_id",
                "DROP INDEX IF EXISTS idx_users_created_at",
                "DROP INDEX IF EXISTS idx_users_active",
                "DROP INDEX IF EXISTS idx_users_role",
                "DROP INDEX IF EXISTS idx_users_username",
                "DROP INDEX IF EXISTS idx_users_email"
            ]
        },
        
        {
            "version": "003_add_audit_triggers",
            "description": "Add audit triggers for tracking data changes",
            "checksum": "c3d4e5f6g7h8",
            "up_sql": [
                # Create audit log table
                """
                CREATE TABLE audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name VARCHAR(100) NOT NULL,
                    operation VARCHAR(10) NOT NULL,
                    record_id INTEGER NOT NULL,
                    old_values TEXT,
                    new_values TEXT,
                    changed_by VARCHAR(255),
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(45),
                    user_agent TEXT
                )
                """,
                
                # Create trigger functions (SQLite doesn't support stored procedures,
                # so we'll use application-level auditing instead)
                
                # Add audit columns to main tables
                """
                ALTER TABLE users ADD COLUMN created_by VARCHAR(255)
                """,
                """
                ALTER TABLE users ADD COLUMN updated_by VARCHAR(255)
                """,
                """
                ALTER TABLE meal_logs ADD COLUMN created_by VARCHAR(255)
                """,
                """
                ALTER TABLE meal_logs ADD COLUMN updated_by VARCHAR(255)
                """,
                """
                ALTER TABLE food_waste_logs ADD COLUMN created_by VARCHAR(255)
                """,
                """
                ALTER TABLE food_waste_logs ADD COLUMN updated_by VARCHAR(255)
                """,
                """
                ALTER TABLE feedback ADD COLUMN created_by VARCHAR(255)
                """,
                """
                ALTER TABLE feedback ADD COLUMN updated_by VARCHAR(255)
                """,
                
                # Create index for audit log
                "CREATE INDEX idx_audit_log_table_name ON audit_log(table_name)",
                "CREATE INDEX idx_audit_log_operation ON audit_log(operation)",
                "CREATE INDEX idx_audit_log_changed_at ON audit_log(changed_at)"
            ],
            "down_sql": [
                "DROP INDEX IF EXISTS idx_audit_log_changed_at",
                "DROP INDEX IF EXISTS idx_audit_log_operation",
                "DROP INDEX IF EXISTS idx_audit_log_table_name",
                "DROP TABLE IF EXISTS audit_log",
                "ALTER TABLE feedback DROP COLUMN updated_by",
                "ALTER TABLE feedback DROP COLUMN created_by",
                "ALTER TABLE food_waste_logs DROP COLUMN updated_by",
                "ALTER TABLE food_waste_logs DROP COLUMN created_by",
                "ALTER TABLE meal_logs DROP COLUMN updated_by",
                "ALTER TABLE meal_logs DROP COLUMN created_by",
                "ALTER TABLE users DROP COLUMN updated_by",
                "ALTER TABLE users DROP COLUMN created_by"
            ]
        },
        
        {
            "version": "004_add_user_preferences",
            "description": "Enhance user preferences with structured data",
            "checksum": "d4e5f6g7h8i9",
            "up_sql": [
                # Create user preferences table
                """
                CREATE TABLE user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    theme VARCHAR(20) DEFAULT 'light',
                    language VARCHAR(10) DEFAULT 'en',
                    timezone VARCHAR(50) DEFAULT 'UTC',
                    email_notifications BOOLEAN DEFAULT TRUE,
                    push_notifications BOOLEAN DEFAULT TRUE,
                    weekly_reports BOOLEAN DEFAULT TRUE,
                    alert_preferences TEXT,
                    dashboard_layout TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """,
                
                # Create index
                "CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id)",
                
                # Migrate existing preferences from users table
                """
                INSERT INTO user_preferences (user_id, theme, email_notifications, weekly_reports)
                SELECT id, 
                       CASE 
                           WHEN preferences LIKE '%theme%' THEN 
                               json_extract(preferences, '$.theme')
                           ELSE 'light'
                       END as theme,
                       CASE 
                           WHEN preferences LIKE '%notifications%' THEN 
                               json_extract(preferences, '$.notifications')
                           ELSE TRUE
                       END as email_notifications,
                       CASE 
                           WHEN preferences LIKE '%reports%' THEN 
                               json_extract(preferences, '$.reports')
                           ELSE TRUE
                       END as weekly_reports
                FROM users 
                WHERE preferences IS NOT NULL
                """
            ],
            "down_sql": [
                "DROP INDEX IF EXISTS idx_user_preferences_user_id",
                "DROP TABLE IF EXISTS user_preferences"
            ]
        },
        
        {
            "version": "005_add_api_keys",
            "description": "Add API key management for external integrations",
            "checksum": "e5f6g7h8i9j0",
            "up_sql": [
                # Create API keys table
                """
                CREATE TABLE api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_name VARCHAR(100) NOT NULL,
                    api_key VARCHAR(255) UNIQUE NOT NULL,
                    key_hash VARCHAR(255) NOT NULL,
                    permissions TEXT NOT NULL,
                    last_used_at DATETIME,
                    expires_at DATETIME,
                    is_active BOOLEAN DEFAULT TRUE NOT NULL,
                    usage_count INTEGER DEFAULT 0 NOT NULL,
                    rate_limit INTEGER DEFAULT 1000,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
                """,
                
                # Create indexes
                "CREATE INDEX idx_api_keys_user_id ON api_keys(user_id)",
                "CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash)",
                "CREATE INDEX idx_api_keys_active ON api_keys(is_active)",
                "CREATE INDEX idx_api_keys_expires_at ON api_keys(expires_at)",
                
                # Create API usage log table
                """
                CREATE TABLE api_usage_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key_id INTEGER NOT NULL,
                    endpoint VARCHAR(255) NOT NULL,
                    method VARCHAR(10) NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    request_size INTEGER,
                    response_size INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE CASCADE
                )
                """,
                
                # Create indexes for usage log
                "CREATE INDEX idx_api_usage_log_api_key_id ON api_usage_log(api_key_id)",
                "CREATE INDEX idx_api_usage_log_created_at ON api_usage_log(created_at)",
                "CREATE INDEX idx_api_usage_log_status_code ON api_usage_log(status_code)"
            ],
            "down_sql": [
                "DROP INDEX IF EXISTS idx_api_usage_log_status_code",
                "DROP INDEX IF EXISTS idx_api_usage_log_created_at",
                "DROP INDEX IF EXISTS idx_api_usage_log_api_key_id",
                "DROP TABLE IF EXISTS api_usage_log",
                "DROP INDEX IF EXISTS idx_api_keys_expires_at",
                "DROP INDEX IF EXISTS idx_api_keys_active",
                "DROP INDEX IF EXISTS idx_api_keys_key_hash",
                "DROP INDEX IF EXISTS idx_api_keys_user_id",
                "DROP TABLE IF EXISTS api_keys"
            ]
        }
    ]
    
    return migrations


def calculate_migration_checksum(migration: Dict[str, Any]) -> str:
    """Calculate checksum for migration to detect changes."""
    content = f"{migration['version']}{migration['description']}"
    if "up_sql" in migration:
        content += "".join(migration["up_sql"])
    if "down_sql" in migration:
        content += "".join(migration["down_sql"])
    
    return hashlib.md5(content.encode()).hexdigest()


def validate_migration(migration: Dict[str, Any]) -> bool:
    """Validate migration structure."""
    required_fields = ["version", "description", "up_sql", "down_sql"]
    
    for field in required_fields:
        if field not in migration:
            return False
    
    # Validate version format
    version = migration["version"]
    if not version or not isinstance(version, str):
        return False
    
    # Validate SQL content
    if not migration["up_sql"] or not isinstance(migration["up_sql"], list):
        return False
    
    if not migration["down_sql"] or not isinstance(migration["down_sql"], list):
        return False
    
    return True


def get_migration_by_version(version: str) -> Optional[Dict[str, Any]]:
    """Get specific migration by version."""
    all_migrations = get_all_migrations()
    
    for migration in all_migrations:
        if migration["version"] == version:
            return migration
    
    return None


def get_latest_version() -> str:
    """Get the latest migration version."""
    all_migrations = get_all_migrations()
    
    if not all_migrations:
        return "000_initial"
    
    return all_migrations[-1]["version"]
