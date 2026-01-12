"""Storage database connection and session management (PostgreSQL or SQLite)."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.settings import settings


def _create_storage_engine():
    """Create the appropriate engine based on storage type."""
    if settings.is_sqlite_storage:
        # SQLite configuration
        # Extract path from connection string if it's a SQLite URL
        db_path = settings.database_url.replace("sqlite:///", "")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
        )
    else:
        # PostgreSQL configuration
        return create_engine(settings.database_url, pool_pre_ping=True)


engine = _create_storage_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_storage_db():
    """Initialize storage database tables."""
    from app.models.starmap import StorageBase
    StorageBase.metadata.create_all(bind=engine)


def get_storage_db() -> Session:
    """Dependency for storage database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_storage_type() -> str:
    """Return current storage type for informational purposes."""
    return settings.storage_type

