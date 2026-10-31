"""Additive schema initializer for existing FreightPilot AI databases.

This compatibility bootstrap creates missing tables and adds the columns needed
by the upgraded API. Use versioned Alembic migrations for future production
schema evolution.
"""

from sqlalchemy import DateTime, Engine, String, inspect, text

from app.db.models import Base
from app.db.session import engine as default_engine

# SQLAlchemy types are compiled against the active dialect so SQLite and
# PostgreSQL receive valid DDL for the same compatibility migration.
_COMPAT_COLUMNS = {
    "shipments": {
        "user_id": (String(36), ""),
        "status": (String(30), "NOT NULL DEFAULT 'DRAFT'"),
    },
    "payments": {
        "provider_refund_id": (String(100), ""),
    },
    "webhook_events": {
        "payload_hash": (String(64), ""),
        "processed_at": (DateTime(timezone=True), ""),
    },
}


def initialize_database(target_engine: Engine = default_engine) -> None:
    """Create missing schema objects and add compatibility columns safely."""
    Base.metadata.create_all(bind=target_engine)
    with target_engine.begin() as connection:
        inspector = inspect(connection)
        table_names = set(inspector.get_table_names())
        for table_name, wanted_columns in _COMPAT_COLUMNS.items():
            if table_name not in table_names:
                continue
            present = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, (column_type, suffix) in wanted_columns.items():
                if column_name not in present:
                    sql_type = column_type.compile(dialect=target_engine.dialect)
                    connection.execute(text(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" '
                        f'{sql_type} {suffix}'.strip()
                    ))

        if "shipments" in table_names:
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_shipments_user_id ON shipments (user_id)"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_shipments_status ON shipments (status)"
            ))

        if "payments" in table_names:
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_payments_provider_refund_id "
                "ON payments (provider_refund_id)"
            ))
            _create_unique_index_if_clean(
                connection, table="payments", column="provider_capture_id",
                index_name="uq_payments_provider_capture_id",
            )
            _create_unique_index_if_clean(
                connection, table="payments", column="idempotency_key",
                index_name="uq_payments_idempotency_key",
            )


def _create_unique_index_if_clean(connection, *, table: str, column: str, index_name: str) -> None:
    """Preserve legacy data; add uniqueness only when no duplicate values exist."""
    duplicate = connection.execute(text(
        f'SELECT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL '
        f'GROUP BY "{column}" HAVING COUNT(*) > 1 LIMIT 1'
    )).first()
    if duplicate is None:
        connection.execute(text(
            f'CREATE UNIQUE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ("{column}")'
        ))


if __name__ == "__main__":
    initialize_database()
    print("FreightPilot AI database schema initialized.")
