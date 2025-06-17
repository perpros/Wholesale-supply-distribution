from pydantic_settings import BaseSettings
from typing import ClassVar

class Settings(BaseSettings):
    SECRET_KEY: str = "your_secret_key"  # Replace with a real secret key in production
    ALGORITHM: ClassVar[str] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database Settings
    # Example: "postgresql://user:password@host:port/dbname"
    # This should be overridden by an environment variable in production.
    DATABASE_URL: str = "postgresql://user:password@localhost/appdb"

    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env" # Optional: if you use a .env file to load these settings
        env_file_encoding = 'utf-8' # Specify encoding for .env file

settings = Settings()
