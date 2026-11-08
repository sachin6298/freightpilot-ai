"""SQLAlchemy engine, declarative base and request-scoped sessions with PostgreSQL support."""

from collections.abc import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from app.config import settings


def create_database_engine() -> create_engine:
    """Create SQLAlchemy engine with appropriate configuration for the database type."""
    engine_options = {
        "pool_pre_ping": True,
        "echo": False,
        "future": True,
    }

    if settings.DATABASE_URL.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
        # Explicitly select psycopg 3 rather than SQLAlchemy's psycopg2 default.
        database_url = settings.DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        engine_options["connect_args"] = {"connect_timeout": 10, "options": "-c timezone=UTC"}
        engine_options.update({
            "poolclass": QueuePool,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
        })
    elif settings.DATABASE_URL.startswith("sqlite"):
        # SQLite-specific configuration for development
        connect_args = {"check_same_thread": False}
        engine_options["connect_args"] = connect_args
    else:
        connect_args = {}

    database_url = locals().get("database_url", settings.DATABASE_URL)
    engine = create_engine(database_url, **engine_options)

    # Database-specific event listeners
    if settings.DATABASE_URL.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _enable_sqlite_foreign_keys(connection, _record) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    elif settings.DATABASE_URL.startswith(("postgresql://", "postgres://", "postgresql+psycopg://")):
        @event.listens_for(engine, "first_connect")
        def _configure_postgresql(connection, _record) -> None:
            # Ensure proper timezone handling
            connection.execute(text("SET TIME ZONE 'UTC'"))

    return engine


engine = create_database_engine()

# Create session factory with appropriate settings
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
