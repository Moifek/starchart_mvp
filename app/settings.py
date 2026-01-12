from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    api_key: str
    
    # Databases
    database_url: str  # PostgreSQL or SQLite connection string
    cache_database_path: str = "data/cache.db"
    
    # Storage type: "postgres" or "sqlite"
    # SQLite example: sqlite:///data/storage.db
    # PostgreSQL example: postgresql://user:pass@localhost:5432/starchart
    storage_type: Literal["postgres", "sqlite"] = "postgres"
    
    # Cache
    cache_max_age_hours: int = 24
    cache_cleanup_interval_minutes: int = 60  # How often to run cleanup
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    @property
    def is_sqlite_storage(self) -> bool:
        """Check if using SQLite for permanent storage."""
        return self.storage_type == "sqlite"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


settings = Settings()

