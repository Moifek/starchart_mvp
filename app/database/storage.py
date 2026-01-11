"""PostgreSQL storage database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.settings import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

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

