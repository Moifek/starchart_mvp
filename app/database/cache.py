"""SQLite cache database connection and session management."""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.settings import settings

# Ensure data directory exists
cache_path = Path(settings.cache_database_path)
cache_path.parent.mkdir(parents=True, exist_ok=True)

# SQLite connection string
CACHE_DATABASE_URL = f"sqlite:///{settings.cache_database_path}"

engine = create_engine(
    CACHE_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite with FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_cache_db():
    """Initialize cache database tables."""
    from app.models.cache import CacheBase
    CacheBase.metadata.create_all(bind=engine)


def get_cache_db() -> Session:
    """Dependency for cache database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

