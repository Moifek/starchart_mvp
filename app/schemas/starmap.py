"""Pydantic schemas for star map request/response validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request schema for star map generation."""
    
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    timezone_offset: int = Field(..., ge=-12, le=14, description="Hours from UTC")
    title: Optional[str] = Field(None, max_length=255)


class SaveRequest(BaseModel):
    """Request schema for saving a cached star map."""
    
    title: Optional[str] = Field(None, max_length=255)


class StarmapResponse(BaseModel):
    """Response schema for saved star map metadata."""
    
    id: UUID
    latitude: float
    longitude: float
    observed_at: datetime
    title: Optional[str]
    created_at: datetime
    
    model_config = {"from_attributes": True}


class StarmapListResponse(BaseModel):
    """Response schema for paginated star map list."""
    
    items: list[StarmapResponse]
    total: int
    skip: int
    limit: int

