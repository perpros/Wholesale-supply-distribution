from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional # Added for SQLALCHEMY_DATABASE_URI

class Settings(BaseSettings):
    PROJECT_NAME: str = "Product Need Request System"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env"  # IMPORTANT: Load from .env in real app
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database - will be used later
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password" # IMPORTANT: Load from .env
    POSTGRES_DB: str = "product_need_system_db"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    # Redis - for Celery, will be used later
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = ".env" # Example: load from .env file if it exists
        env_file_encoding = 'utf-8'
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
