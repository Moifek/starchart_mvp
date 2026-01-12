"""Model for permanent star map storage (PostgreSQL or SQLite compatible)."""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Float, Integer, LargeBinary, DateTime, Index, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR

from app.settings import settings


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type when available, otherwise uses CHAR(36) for SQLite.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, convert UUID to string
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, convert string back to UUID
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value


class JSONType(TypeDecorator):
    """Platform-independent JSON type.
    
    Uses PostgreSQL's JSONB when available, otherwise uses TEXT with JSON serialization for SQLite.
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, serialize to JSON string
        import json
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        # For SQLite, deserialize from JSON string
        import json
        if isinstance(value, str):
            return json.loads(value)
        return value


StorageBase = declarative_base()


class Starmap(StorageBase):
    """Permanently saved star map."""
    
    __tablename__ = "starmaps"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    timezone_offset = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    image_data = Column(LargeBinary, nullable=False)
    extra_data = Column(JSONType(), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_starmaps_location', 'latitude', 'longitude'),
        Index('idx_starmaps_observed', 'observed_at'),
    )

