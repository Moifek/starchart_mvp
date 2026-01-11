from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # API
    api_key: str
    
    # Databases
    database_url: str
    cache_database_path: str = "data/cache.db"
    
    # Cache
    cache_max_age_hours: int = 24
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


settings = Settings()

