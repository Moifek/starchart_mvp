import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.cache import init_cache_db, get_cache_db, SessionLocal as CacheSessionLocal
from app.database.storage import init_storage_db, get_storage_type
from app.routers import starmaps
from app.services.starmap import cleanup_old_cache
from app.settings import settings

logger = logging.getLogger(__name__)

# Flag to control the background task
_cleanup_task_running = False


async def cache_cleanup_task():
    """Background task that periodically cleans up old cache entries."""
    global _cleanup_task_running
    _cleanup_task_running = True
    
    interval_seconds = settings.cache_cleanup_interval_minutes * 60
    max_age_hours = settings.cache_max_age_hours
    
    logger.info(
        f"Cache cleanup task started - running every {settings.cache_cleanup_interval_minutes} minutes, "
        f"removing entries older than {max_age_hours} hours"
    )
    
    while _cleanup_task_running:
        try:
            # Wait first, then cleanup (gives time for system to stabilize on startup)
            await asyncio.sleep(interval_seconds)
            
            if not _cleanup_task_running:
                break
            
            # Run cleanup in a sync context (SQLite session)
            db = CacheSessionLocal()
            try:
                cleanup_old_cache(db, max_age_hours=max_age_hours)
                logger.info("Cache cleanup completed successfully")
            except Exception as e:
                logger.error(f"Cache cleanup failed: {e}")
            finally:
                db.close()
                
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Unexpected error in cache cleanup task: {e}")
            # Continue running despite errors
            await asyncio.sleep(60)  # Brief pause before retrying


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    global _cleanup_task_running
    
    # Startup
    init_cache_db()
    init_storage_db()
    
    logger.info(f"Storage type: {get_storage_type()}")
    
    # Start background cache cleanup task
    cleanup_task = asyncio.create_task(cache_cleanup_task())
    
    yield
    
    # Shutdown - stop the cleanup task gracefully
    _cleanup_task_running = False
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    logger.info("Cache cleanup task stopped")


app = FastAPI(
    title="StarChart API",
    description="Generate beautiful star map images for any date and location",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Shopify frontend integration
# 
# PRODUCTION: Uncomment and configure these restricted origins:
# ALLOWED_ORIGINS = [
#     "https://your-store.myshopify.com",
#     "https://your-custom-domain.com",
# ]
#
# DEVELOPMENT: Allow all origins (current setting)
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type"],
    expose_headers=["X-Cache-Id", "X-Cache-Hit"],  # Allow JS to read these response headers
)

# Include routers
app.include_router(starmaps.router, prefix="/api/v1/starmaps", tags=["starmaps"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "storage_type": get_storage_type(),
        "cache_cleanup_interval_minutes": settings.cache_cleanup_interval_minutes,
        "cache_max_age_hours": settings.cache_max_age_hours
    }

