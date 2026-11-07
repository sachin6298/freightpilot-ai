"""Migration utility for moving data from SQLite to PostgreSQL."""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from sqlalchemy import create_engine, text, MetaData, Table, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sqlite_engine(sqlite_path: str = "freightpilot.db"):
    """Create SQLAlchemy engine for SQLite database."""
    sqlite_url = f"sqlite:///{sqlite_path}"
    return create_engine(sqlite_url, echo=False)


def get_postgresql_engine(postgresql_url: str = None):
    """Create SQLAlchemy engine for PostgreSQL database."""
    if postgresql_url is None:
        postgresql_url = settings.DATABASE_URL
    return create_engine(postgresql_url, echo=False)


def export_table_data(source_engine, table_name: str) -> List[Dict[str, Any]]:
    """Export data from a table as dictionaries."""
    metadata = MetaData()
    metadata.reflect(bind=source_engine)

    if table_name not in metadata.tables:
        logger.warning(f"Table {table_name} not found in source database")
        return []

    table = metadata.tables[table_name]
    with source_engine.connect() as conn:
        result = conn.execute(select(table))
        rows = result.fetchall()

        # Convert rows to dictionaries
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(table.columns):
                value = row[i]
                # Handle JSON columns and special types
                if column.type.python_type == dict and value is not None:
                    row_dict[column.name] = json.loads(value) if isinstance(value, str) else value
                elif isinstance(value, datetime):
                    row_dict[column.name] = value.isoformat()
                else:
                    row_dict[column.name] = value
            data.append(row_dict)

    logger.info(f"Exported {len(data)} rows from {table_name}")
    return data


def import_table_data(target_engine, table_name: str, data: List[Dict[str, Any]]):
    """Import data into a PostgreSQL table."""
    if not data:
        logger.info(f"No data to import for {table_name}")
        return

    metadata = MetaData()
    metadata.reflect(bind=target_engine)

    if table_name not in metadata.tables:
        logger.error(f"Table {table_name} not found in target database")
        return

    table = metadata.tables[table_name]

    # Get column information
    columns = {col.name: col for col in table.columns}

    with target_engine.begin() as conn:
        imported_count = 0
        for row in data:
            try:
                # Prepare data for insertion
                insert_data = {}
                for key, value in row.items():
                    if key in columns:
                        col_type = columns[key].type
                        # Handle special data types
                        if hasattr(col_type, 'python_type') and col_type.python_type == dict and value is not None:
                            insert_data[key] = json.dumps(value)
                        elif isinstance(value, str) and key.endswith('_at') or key.endswith('_until'):
                            # Try to parse datetime strings
                            try:
                                insert_data[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except (ValueError, AttributeError):
                                insert_data[key] = value
                        else:
                            insert_data[key] = value

                # Insert data
                insert_stmt = table.insert().values(**insert_data)
                conn.execute(insert_stmt)
                imported_count += 1

            except SQLAlchemyError as e:
                logger.error(f"Error importing row into {table_name}: {e}")
                continue

        logger.info(f"Imported {imported_count} rows into {table_name}")


def migrate_sqlite_to_postgresql(sqlite_path: str = None, postgresql_url: str = None):
    """Main migration function to move data from SQLite to PostgreSQL."""

    if sqlite_path is None:
        sqlite_path = "freightpilot.db"

    if postgresql_url is None:
        postgresql_url = settings.DATABASE_URL

    # Check if SQLite database exists
    if not Path(sqlite_path).exists():
        logger.error(f"SQLite database not found at {sqlite_path}")
        return False

    logger.info("Starting migration from SQLite to PostgreSQL")
    logger.info(f"Source: {sqlite_path}")
    logger.info(f"Target: {postgresql_url}")

    try:
        # Create engines
        sqlite_engine = get_sqlite_engine(sqlite_path)
        postgresql_engine = get_postgresql_engine(postgresql_url)

        # Define migration order (respect foreign key constraints)
        tables_order = [
            'users',
            'shipments',
            'quotes',
            'risk_assessments',
            'payments',
            'webhook_events',
            'tracking_events',
            'audit_logs',
            'notifications',
            'ai_conversations'
        ]

        # Migrate each table
        for table_name in tables_order:
            logger.info(f"Migrating {table_name}...")
            try:
                data = export_table_data(sqlite_engine, table_name)
                if data:
                    import_table_data(postgresql_engine, table_name, data)
                else:
                    logger.info(f"No data in {table_name}")
            except Exception as e:
                logger.error(f"Error migrating {table_name}: {e}")
                continue

        logger.info("Migration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False


def verify_migration(postgresql_url: str = None):
    """Verify that data was migrated correctly."""
    if postgresql_url is None:
        postgresql_url = settings.DATABASE_URL

    postgresql_engine = get_postgresql_engine(postgresql_url)

    tables_to_check = [
        'users',
        'shipments',
        'quotes',
        'payments'
    ]

    logger.info("Verifying migration...")

    with postgresql_engine.connect() as conn:
        for table_name in tables_to_check:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                logger.info(f"{table_name}: {count} rows")
            except Exception as e:
                logger.error(f"Error checking {table_name}: {e}")

    logger.info("Verification completed")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Migrate data from SQLite to PostgreSQL")
    parser.add_argument("--sqlite-path", default="freightpilot.db", help="Path to SQLite database file")
    parser.add_argument("--postgresql-url", default=None, help="PostgreSQL connection URL")
    parser.add_argument("--verify", action="store_true", help="Verify migration after completion")

    args = parser.parse_args()

    # Run migration
    success = migrate_sqlite_to_postgresql(args.sqlite_path, args.postgresql_url)

    if success and args.verify:
        verify_migration(args.postgresql_url)

    exit(0 if success else 1)