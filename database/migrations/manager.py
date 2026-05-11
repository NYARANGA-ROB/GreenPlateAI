"""
Migration manager for GreenPlateAI database.

This module provides comprehensive migration management with
version tracking, rollback capabilities, and automated migration execution.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..init_db import db_manager

logger = logging.getLogger(__name__)


class MigrationManager:
    """Advanced migration manager for database schema changes."""
    
    def __init__(self, db_manager=None):
        """Initialize migration manager."""
        self.db_manager = db_manager or db_manager
        self.migrations_dir = os.path.dirname(os.path.abspath(__file__))
        
    def ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        try:
            session = self.db_manager.get_session()
            
            # Create migration tracking table if not exists
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    checksum VARCHAR(64)
                )
            """))
            
            # Create migration lock table for concurrent execution safety
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS migration_lock (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    locked BOOLEAN DEFAULT FALSE,
                    locked_by VARCHAR(255),
                    locked_at DATETIME,
                    CONSTRAINT single_lock CHECK (id = 1)
                )
            """))
            
            # Ensure single lock record exists
            session.execute(text("""
                INSERT OR IGNORE INTO migration_lock (id, locked) VALUES (1, FALSE)
            """))
            
            session.commit()
            logger.info("Migration tables ensured")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to ensure migration tables: {e}")
            raise
        finally:
            session.close()
    
    def acquire_migration_lock(self, lock_holder: str = "migration_system") -> bool:
        """Acquire migration lock for safe concurrent execution."""
        try:
            session = self.db_manager.get_session()
            
            # Try to acquire lock
            result = session.execute(text("""
                UPDATE migration_lock 
                SET locked = TRUE, locked_by = :holder, locked_at = :timestamp
                WHERE id = 1 AND locked = FALSE
            """), {
                "holder": lock_holder,
                "timestamp": datetime.utcnow()
            })
            
            session.commit()
            
            # Check if lock was acquired
            if result.rowcount > 0:
                logger.info(f"Migration lock acquired by {lock_holder}")
                return True
            else:
                # Check who holds the lock
                lock_info = session.execute(text("""
                    SELECT locked_by, locked_at FROM migration_lock WHERE id = 1
                """)).fetchone()
                
                logger.warning(f"Migration lock held by {lock_info[0]} since {lock_info[1]}")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to acquire migration lock: {e}")
            return False
        finally:
            session.close()
    
    def release_migration_lock(self) -> bool:
        """Release migration lock."""
        try:
            session = self.db_manager.get_session()
            
            session.execute(text("""
                UPDATE migration_lock 
                SET locked = FALSE, locked_by = NULL, locked_at = NULL
                WHERE id = 1
            """))
            
            session.commit()
            logger.info("Migration lock released")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to release migration lock: {e}")
            return False
        finally:
            session.close()
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations."""
        try:
            session = self.db_manager.get_session()
            
            result = session.execute(text("""
                SELECT version, description, applied_at, execution_time_ms, checksum
                FROM schema_migrations 
                ORDER BY applied_at
            """))
            
            migrations = []
            for row in result:
                migrations.append({
                    "version": row[0],
                    "description": row[1],
                    "applied_at": row[2],
                    "execution_time_ms": row[3],
                    "checksum": row[4]
                })
            
            session.close()
            return migrations
            
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def is_migration_applied(self, version: str) -> bool:
        """Check if a specific migration version has been applied."""
        try:
            session = self.db_manager.get_session()
            
            result = session.execute(text("""
                SELECT 1 FROM schema_migrations WHERE version = :version
            """), {"version": version})
            
            applied = result.fetchone() is not None
            session.close()
            
            return applied
            
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False
    
    def apply_migration(self, migration: Dict[str, Any]) -> bool:
        """Apply a single migration."""
        try:
            if not self.acquire_migration_lock():
                logger.error("Could not acquire migration lock")
                return False
            
            start_time = datetime.utcnow()
            
            # Check if already applied
            if self.is_migration_applied(migration["version"]):
                logger.info(f"Migration {migration['version']} already applied")
                return True
            
            session = self.db_manager.get_session()
            
            # Start transaction
            session.begin()
            
            try:
                # Execute migration SQL
                if "up_sql" in migration and migration["up_sql"]:
                    for sql_statement in migration["up_sql"]:
                        if sql_statement.strip():
                            session.execute(text(sql_statement))
                
                # Record migration
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                session.execute(text("""
                    INSERT INTO schema_migrations 
                    (version, description, applied_at, execution_time_ms, checksum)
                    VALUES (:version, :description, :applied_at, :execution_time, :checksum)
                """), {
                    "version": migration["version"],
                    "description": migration.get("description", ""),
                    "applied_at": start_time,
                    "execution_time": execution_time,
                    "checksum": migration.get("checksum", "")
                })
                
                session.commit()
                logger.info(f"Migration {migration['version']} applied successfully in {execution_time}ms")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to apply migration {migration['version']}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            return False
        finally:
            self.release_migration_lock()
    
    def rollback_migration(self, migration: Dict[str, Any]) -> bool:
        """Rollback a migration."""
        try:
            if not self.acquire_migration_lock():
                logger.error("Could not acquire migration lock")
                return False
            
            # Check if migration is applied
            if not self.is_migration_applied(migration["version"]):
                logger.info(f"Migration {migration['version']} is not applied, cannot rollback")
                return True
            
            session = self.db_manager.get_session()
            
            # Start transaction
            session.begin()
            
            try:
                # Execute rollback SQL
                if "down_sql" in migration and migration["down_sql"]:
                    for sql_statement in migration["down_sql"]:
                        if sql_statement.strip():
                            session.execute(text(sql_statement))
                
                # Remove migration record
                session.execute(text("""
                    DELETE FROM schema_migrations WHERE version = :version
                """), {"version": migration["version"]})
                
                session.commit()
                logger.info(f"Migration {migration['version']} rolled back successfully")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to rollback migration {migration['version']}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Rollback execution failed: {e}")
            return False
        finally:
            self.release_migration_lock()
    
    def get_pending_migrations(self, all_migrations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get list of pending migrations."""
        applied_versions = {m["version"] for m in self.get_applied_migrations()}
        
        pending = []
        for migration in all_migrations:
            if migration["version"] not in applied_versions:
                pending.append(migration)
        
        # Sort by version
        pending.sort(key=lambda x: x["version"])
        return pending
    
    def migrate_up(self, target_version: str = None) -> bool:
        """Migrate up to a specific version or latest."""
        try:
            # Get all available migrations
            from .versions import get_all_migrations
            all_migrations = get_all_migrations()
            
            # Get pending migrations
            pending = self.get_pending_migrations(all_migrations)
            
            # Filter by target version if specified
            if target_version:
                pending = [m for m in pending if m["version"] <= target_version]
            
            if not pending:
                logger.info("No pending migrations to apply")
                return True
            
            logger.info(f"Applying {len(pending)} pending migrations")
            
            # Apply migrations in order
            for migration in pending:
                if not self.apply_migration(migration):
                    logger.error(f"Migration failed at version {migration['version']}")
                    return False
            
            logger.info("All migrations applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration up failed: {e}")
            return False
    
    def migrate_down(self, target_version: str) -> bool:
        """Migrate down to a specific version."""
        try:
            # Get all available migrations
            from .versions import get_all_migrations
            all_migrations = get_all_migrations()
            
            # Get applied migrations
            applied = self.get_applied_migrations()
            
            # Find migrations to rollback
            to_rollback = []
            for applied_migration in reversed(applied):
                if applied_migration["version"] > target_version:
                    # Find corresponding migration definition
                    for migration in all_migrations:
                        if migration["version"] == applied_migration["version"]:
                            to_rollback.append(migration)
                            break
            
            if not to_rollback:
                logger.info(f"No migrations to rollback to version {target_version}")
                return True
            
            logger.info(f"Rolling back {len(to_rollback)} migrations")
            
            # Rollback migrations in reverse order
            for migration in to_rollback:
                if not self.rollback_migration(migration):
                    logger.error(f"Rollback failed at version {migration['version']}")
                    return False
            
            logger.info(f"Successfully rolled back to version {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Migration down failed: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        try:
            from .versions import get_all_migrations
            all_migrations = get_all_migrations()
            applied_migrations = self.get_applied_migrations()
            pending_migrations = self.get_pending_migrations(all_migrations)
            
            applied_versions = {m["version"] for m in applied_migrations}
            
            # Find current version
            current_version = None
            if applied_versions:
                current_version = max(applied_versions)
            
            return {
                "current_version": current_version,
                "total_migrations": len(all_migrations),
                "applied_count": len(applied_migrations),
                "pending_count": len(pending_migrations),
                "applied_migrations": applied_migrations,
                "pending_migrations": [m["version"] for m in pending_migrations],
                "status": "up_to_date" if len(pending_migrations) == 0 else "pending_migrations"
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}
    
    def validate_migrations(self) -> Dict[str, Any]:
        """Validate migration integrity."""
        try:
            from .versions import get_all_migrations
            all_migrations = get_all_migrations()
            applied_migrations = self.get_applied_migrations()
            
            validation_results = {
                "valid": True,
                "issues": [],
                "warnings": []
            }
            
            # Check for duplicate versions
            versions = [m["version"] for m in all_migrations]
            if len(versions) != len(set(versions)):
                validation_results["valid"] = False
                validation_results["issues"].append("Duplicate migration versions found")
            
            # Check for missing rollback SQL
            for migration in all_migrations:
                if "down_sql" not in migration or not migration["down_sql"]:
                    validation_results["warnings"].append(f"Migration {migration['version']} missing rollback SQL")
            
            # Check for applied migrations that don't exist
            applied_versions = {m["version"] for m in applied_migrations}
            available_versions = set(versions)
            
            orphaned = applied_versions - available_versions
            if orphaned:
                validation_results["warnings"].append(f"Orphaned applied migrations: {orphaned}")
            
            return validation_results
            
        except Exception as e:
            return {"valid": False, "issues": [str(e)]}


# Global migration manager instance
migration_manager = MigrationManager()


def get_migration_manager() -> MigrationManager:
    """Get global migration manager instance."""
    return migration_manager
