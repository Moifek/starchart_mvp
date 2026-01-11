"""SQLite cache model for temporary star map storage."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, LargeBinary, DateTime, Index
from sqlalchemy.orm import declarative_base

CacheBase = declarative_base()


class CachedStarmap(CacheBase):
    """Cached star map for fast retrieval during user exploration."""
    
    __tablename__ = "cached_starmaps"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    hour = Column(Integer, nullable=False)
    minute = Column(Integer, nullable=False)
    timezone_offset = Column(Integer, nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cache_lookup', 'latitude', 'longitude', 'year', 'month', 'day', 'hour'),
        Index('idx_cache_created_at', 'created_at'),
    )

