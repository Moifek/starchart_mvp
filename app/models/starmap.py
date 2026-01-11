"""PostgreSQL model for permanent star map storage."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, LargeBinary, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

StorageBase = declarative_base()


class Starmap(StorageBase):
    """Permanently saved star map."""
    
    __tablename__ = "starmaps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    timezone_offset = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    image_data = Column(LargeBinary, nullable=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_starmaps_location', 'latitude', 'longitude'),
        Index('idx_starmaps_observed', 'observed_at'),
    )

