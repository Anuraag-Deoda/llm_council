"""
Database session management
"""
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from app.config import settings
from app.database.models import Base
# Import RAG models to register them with Base.metadata
from app.database import rag_models  # noqa: F401

logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=settings.database_echo,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Connection event listeners for better debugging
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections"""
    logger.debug("Database connection established")


@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    """Log database disconnections"""
    logger.debug("Database connection closed")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions

    Usage:
        @app.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables

    This should be called on application startup.
    Handles race conditions when multiple workers start simultaneously.
    """
    from sqlalchemy.exc import ProgrammingError
    from psycopg2.errors import UniqueViolation, DuplicateTable, DuplicateObject

    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        # Handle race condition where multiple workers try to create
        # the same types/tables simultaneously
        error_str = str(e)
        if (
            isinstance(e.__cause__, (UniqueViolation, DuplicateTable, DuplicateObject))
            or "already exists" in error_str.lower()
            or "duplicate key" in error_str.lower()
        ):
            logger.info("Database already initialized by another worker")
        else:
            logger.error(f"Failed to initialize database: {e}")
            raise


def close_db() -> None:
    """
    Close database connections

    This should be called on application shutdown
    """
    try:
        logger.info("Closing database connections...")
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
