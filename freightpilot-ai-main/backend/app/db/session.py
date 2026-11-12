
"""SQLAlchemy engine, declarative base and request-scoped sessions with PostgreSQL support."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import settings


def create_database_engine():
    """Create SQLAlchemy engine with appropriate database configuration."""

    engine_options = {
        "pool_pre_ping": True,
        "echo": False,
        "future": True,
    }

    database_url = settings.DATABASE_URL

    # PostgreSQL configuration (Neon supported)
    if database_url.startswith(
        ("postgresql://", "postgres://", "postgresql+psycopg://")
    ):
        database_url = database_url.replace(
            "postgres://", "postgresql+psycopg://", 1
        )

        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        engine_options["connect_args"] = {
            "connect_timeout": 10,
            "options": "-c timezone=UTC",
        }

        engine_options.update({
            "poolclass": QueuePool,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        })

    # SQLite configuration (local development)
    elif database_url.startswith("sqlite"):
        engine_options["connect_args"] = {
            "check_same_thread": False
        }

    engine = create_engine(database_url, **engine_options)

    # SQLite-specific connection settings
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    # PostgreSQL-specific connection settings
    elif database_url.startswith(
        ("postgresql://", "postgres://", "postgresql+psycopg://")
    ):

        @event.listens_for(engine, "connect")
        def _configure_postgresql(dbapi_connection, _record):
            """Set PostgreSQL connection timezone to UTC."""
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET TIME ZONE 'UTC'")

    return engine


# Database engine
engine = create_database_engine()


# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


# Declarative model base
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Provide a request-scoped database session."""

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
