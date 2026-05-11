"""
Command-line interface for database migrations.

This module provides CLI commands for managing database migrations
including up, down, status, and validation operations.
"""

import argparse
import sys
import logging
from typing import Optional

from .manager import get_migration_manager
from .versions import get_all_migrations, get_latest_version

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_up(target_version: Optional[str] = None) -> bool:
    """Migrate database up to target version."""
    try:
        manager = get_migration_manager()
        manager.ensure_migration_table()
        
        if target_version:
            logger.info(f"Migrating up to version {target_version}")
        else:
            logger.info("Migrating up to latest version")
        
        success = manager.migrate_up(target_version)
        
        if success:
            logger.info("✅ Migration completed successfully")
            return True
        else:
            logger.error("❌ Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False


def migrate_down(target_version: str) -> bool:
    """Migrate database down to target version."""
    try:
        manager = get_migration_manager()
        manager.ensure_migration_table()
        
        logger.info(f"Migrating down to version {target_version}")
        
        success = manager.migrate_down(target_version)
        
        if success:
            logger.info("✅ Rollback completed successfully")
            return True
        else:
            logger.error("❌ Rollback failed")
            return False
            
    except Exception as e:
        logger.error(f"Rollback error: {e}")
        return False


def show_status() -> bool:
    """Show migration status."""
    try:
        manager = get_migration_manager()
        manager.ensure_migration_table()
        
        status = manager.get_migration_status()
        
        if "error" in status:
            logger.error(f"❌ Error getting status: {status['error']}")
            return False
        
        print("\n📊 Migration Status")
        print("=" * 50)
        print(f"Current Version: {status.get('current_version', 'None')}")
        print(f"Total Migrations: {status.get('total_migrations', 0)}")
        print(f"Applied: {status.get('applied_count', 0)}")
        print(f"Pending: {status.get('pending_count', 0)}")
        print(f"Status: {status.get('status', 'unknown')}")
        
        if status.get('pending_migrations'):
            print("\n⏳ Pending Migrations:")
            for version in status['pending_migrations']:
                print(f"  - {version}")
        
        if status.get('applied_migrations'):
            print("\n✅ Applied Migrations:")
            for migration in status['applied_migrations'][-5:]:  # Show last 5
                print(f"  - {migration['version']} ({migration['applied_at']})")
        
        return True
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return False


def validate_migrations() -> bool:
    """Validate migration integrity."""
    try:
        manager = get_migration_manager()
        
        validation = manager.validate_migrations()
        
        print("\n🔍 Migration Validation")
        print("=" * 50)
        
        if validation['valid']:
            print("✅ All migrations are valid")
        else:
            print("❌ Migration validation failed")
            
        if validation['issues']:
            print("\n🚨 Issues:")
            for issue in validation['issues']:
                print(f"  - {issue}")
        
        if validation['warnings']:
            print("\n⚠️ Warnings:")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        return validation['valid']
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return False


def list_migrations() -> bool:
    """List all available migrations."""
    try:
        migrations = get_all_migrations()
        
        print("\n📋 Available Migrations")
        print("=" * 50)
        
        for migration in migrations:
            status = "✅ Applied" if get_migration_manager().is_migration_applied(migration['version']) else "⏳ Pending"
            print(f"{status} {migration['version']} - {migration['description']}")
        
        return True
        
    except Exception as e:
        logger.error(f"List error: {e}")
        return False


def create_migration(name: str) -> bool:
    """Create a new migration template."""
    try:
        from datetime import datetime
        import os
        
        # Generate migration version
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{name.lower().replace(' ', '_')}"
        
        # Generate migration template
        template = f'''"""
{{
    "version": "{version}",
    "description": "{name}",
    "checksum": "",
    "up_sql": [
        "-- Add your UP migration SQL here"
    ],
    "down_sql": [
        "-- Add your DOWN migration SQL here"
    ]
}}
'''
        
        # Save to file (in a real implementation)
        migrations_dir = os.path.join(os.path.dirname(__file__), "custom")
        os.makedirs(migrations_dir, exist_ok=True)
        
        migration_file = os.path.join(migrations_dir, f"{version}.py")
        with open(migration_file, 'w') as f:
            f.write(template)
        
        print(f"✅ Migration template created: {migration_file}")
        print("📝 Edit the file to add your migration SQL")
        
        return True
        
    except Exception as e:
        logger.error(f"Create migration error: {e}")
        return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GreenPlateAI Database Migration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m database.migrations.cli up                    # Migrate to latest
  python -m database.migrations.cli up 002_add_indexes    # Migrate to specific version
  python -m database.migrations.cli down 001_initial_schema  # Rollback to version
  python -m database.migrations.cli status               # Show migration status
  python -m database.migrations.cli validate             # Validate migrations
  python -m database.migrations.cli list                 # List all migrations
  python -m database.migrations.cli create "add_new_table"  # Create migration template
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Up command
    up_parser = subparsers.add_parser('up', help='Migrate database up')
    up_parser.add_argument('version', nargs='?', help='Target version (optional)')
    up_parser.set_defaults(func=lambda args: migrate_up(args.version))
    
    # Down command
    down_parser = subparsers.add_parser('down', help='Migrate database down')
    down_parser.add_argument('version', help='Target version')
    down_parser.set_defaults(func=lambda args: migrate_down(args.version))
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show migration status')
    status_parser.set_defaults(func=lambda args: show_status())
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate migrations')
    validate_parser.set_defaults(func=lambda args: validate_migrations())
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all migrations')
    list_parser.set_defaults(func=lambda args: list_migrations())
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new migration')
    create_parser.add_argument('name', help='Migration name')
    create_parser.set_defaults(func=lambda args: create_migration(args.name))
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    success = args.func(args)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
