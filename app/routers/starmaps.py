"""Star map API endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database.cache import get_cache_db
from app.database.storage import get_storage_db
from app.dependencies import verify_api_key
from app.schemas.starmap import (
    GenerateRequest,
    SaveRequest,
    StarmapListResponse,
    StarmapResponse,
)
from app.services import starmap as starmap_service

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/generate")
async def generate_starmap(
    request: GenerateRequest,
    db_cache: Session = Depends(get_cache_db)
) -> Response:
    """
    Generate a star map image for the given location and time.
    
    Returns PNG image with cache headers.
    """
    image_data, cache_id, cache_hit = starmap_service.generate_or_get_cached(
        db_cache=db_cache,
        request=request
    )
    
    return Response(
        content=image_data,
        media_type="image/png",
        headers={
            "X-Cache-Id": cache_id,
            "X-Cache-Hit": str(cache_hit).lower()
        }
    )


@router.post("/{cache_id}/save", response_model=StarmapResponse)
async def save_starmap(
    cache_id: str,
    request: SaveRequest = None,
    db_cache: Session = Depends(get_cache_db),
    db_storage: Session = Depends(get_storage_db)
) -> StarmapResponse:
    """
    Save a cached star map to permanent storage.
    
    Uses the cache_id from the X-Cache-Id header of the generate response.
    """
    if request is None:
        request = SaveRequest()
    
    try:
        starmap = starmap_service.save_to_storage(
            db_cache=db_cache,
            db_storage=db_storage,
            cache_id=cache_id,
            title=request.title
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cache entry {cache_id} not found"
        )
    
    return StarmapResponse.model_validate(starmap)


@router.get("/{starmap_id}")
async def get_starmap(
    starmap_id: UUID,
    db_storage: Session = Depends(get_storage_db)
) -> Response:
    """
    Get a saved star map image by ID.
    
    Returns PNG image.
    """
    starmap = starmap_service.get_by_id(db=db_storage, starmap_id=starmap_id)
    
    if not starmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star map not found"
        )
    
    return Response(
        content=starmap.image_data,
        media_type="image/png"
    )


@router.get("", response_model=StarmapListResponse)
async def list_starmaps(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db_storage: Session = Depends(get_storage_db)
) -> StarmapListResponse:
    """
    List saved star maps with pagination.
    """
    items, total = starmap_service.list_starmaps(
        db=db_storage,
        skip=skip,
        limit=limit
    )
    
    return StarmapListResponse(
        items=[StarmapResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit
    )


@router.delete("/{starmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_starmap(
    starmap_id: UUID,
    db_storage: Session = Depends(get_storage_db)
):
    """
    Delete a saved star map.
    """
    deleted = starmap_service.delete_starmap(db=db_storage, starmap_id=starmap_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Star map not found"
        )
    
    return None

