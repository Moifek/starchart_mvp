"""Business logic layer for star map operations."""
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cache import CachedStarmap
from app.models.starmap import Starmap
from app.schemas.starmap import GenerateRequest
from app.services.generator import generator


def _round_coords(lat: float, lon: float) -> Tuple[float, float]:
    """Round coordinates for cache key consistency."""
    return round(lat, 4), round(lon, 4)


def generate_or_get_cached(
    db_cache: Session,
    request: GenerateRequest
) -> Tuple[bytes, str, bool]:
    """
    Generate star map or return from cache.
    
    Returns:
        Tuple of (image_bytes, cache_id, cache_hit)
    """
    lat, lon = _round_coords(request.latitude, request.longitude)
    
    # Check cache
    cached = db_cache.query(CachedStarmap).filter(
        CachedStarmap.latitude == lat,
        CachedStarmap.longitude == lon,
        CachedStarmap.year == request.year,
        CachedStarmap.month == request.month,
        CachedStarmap.day == request.day,
        CachedStarmap.hour == request.hour,
        CachedStarmap.minute == request.minute,
        CachedStarmap.timezone_offset == request.timezone_offset
    ).first()
    
    if cached:
        return cached.image_data, cached.id, True
    
    # Generate new image
    image_data = generator.generate(
        latitude=lat,
        longitude=lon,
        year=request.year,
        month=request.month,
        day=request.day,
        hour=request.hour,
        minute=request.minute,
        timezone_offset=request.timezone_offset,
        title=request.title or "THE NIGHT SKY"
    )
    
    # Store in cache
    new_cached = CachedStarmap(
        latitude=lat,
        longitude=lon,
        year=request.year,
        month=request.month,
        day=request.day,
        hour=request.hour,
        minute=request.minute,
        timezone_offset=request.timezone_offset,
        image_data=image_data
    )
    db_cache.add(new_cached)
    db_cache.commit()
    db_cache.refresh(new_cached)
    
    return image_data, new_cached.id, False


def save_to_storage(
    db_cache: Session,
    db_storage: Session,
    cache_id: str,
    title: Optional[str] = None
) -> Starmap:
    """
    Save cached starmap to permanent storage.
    
    Raises:
        ValueError: If cache_id not found
    """
    cached = db_cache.query(CachedStarmap).filter(
        CachedStarmap.id == cache_id
    ).first()
    
    if not cached:
        raise ValueError(f"Cache entry {cache_id} not found")
    
    # Create observed_at datetime
    tz = timezone(timedelta(hours=cached.timezone_offset))
    observed_at = datetime(
        cached.year, cached.month, cached.day,
        cached.hour, cached.minute, tzinfo=tz
    )
    
    # Insert to PostgreSQL
    starmap = Starmap(
        latitude=cached.latitude,
        longitude=cached.longitude,
        observed_at=observed_at,
        timezone_offset=cached.timezone_offset,
        title=title,
        image_data=cached.image_data
    )
    db_storage.add(starmap)
    db_storage.commit()
    db_storage.refresh(starmap)
    
    return starmap


def get_by_id(db: Session, starmap_id: UUID) -> Optional[Starmap]:
    """Get starmap from permanent storage by ID."""
    return db.query(Starmap).filter(Starmap.id == starmap_id).first()


def list_starmaps(db: Session, skip: int = 0, limit: int = 20) -> Tuple[list[Starmap], int]:
    """List starmaps with pagination."""
    total = db.query(Starmap).count()
    items = db.query(Starmap).order_by(Starmap.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def delete_starmap(db: Session, starmap_id: UUID) -> bool:
    """Delete starmap from permanent storage."""
    starmap = db.query(Starmap).filter(Starmap.id == starmap_id).first()
    if starmap:
        db.delete(starmap)
        db.commit()
        return True
    return False


def cleanup_old_cache(db_cache: Session, max_age_hours: int = 24):
    """Remove cache entries older than max_age_hours."""
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    db_cache.query(CachedStarmap).filter(
        CachedStarmap.created_at < cutoff
    ).delete()
    db_cache.commit()

