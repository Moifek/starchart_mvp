from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.cache import init_cache_db
from app.database.storage import init_storage_db
from app.routers import starmaps
from app.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    init_cache_db()
    init_storage_db()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="StarChart API",
    description="Generate beautiful star map images for any date and location",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Shopify frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your Shopify domain in production
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# Include routers
app.include_router(starmaps.router, prefix="/api/v1/starmaps", tags=["starmaps"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

