"""
Application Configuration Module.

Loads settings from environment variables and/or a .env file.
Provides a centralized `Settings` object.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings.

    These settings are loaded from environment variables or a .env file.
    """
    PROJECT_NAME: str = "Product Need Request System"
    API_V1_STR: str = "/api/v1"

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "product_need_db" # Default DB name, can be overridden by .env
    DATABASE_URL: str | None = None # Can be set directly, otherwise constructed

    # Security settings
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed_in_production" # IMPORTANT: Change this!
    ALGORITHM: str = "HS256" # Algorithm for JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 # Lifetime of access tokens

    class Config:
        """
        Pydantic BaseSettings configuration.
        Specifies the .env file to load environment variables from.
        """
        env_file = ".env" # Looks for .env in the directory where the app is run
        env_file_encoding = 'utf-8'
        # For Pydantic v1, case_sensitive = True by default.
        # For Pydantic v2, the default is case_sensitive = settings.case_sensitive.
        # Environment variables are typically uppercase, so this should align.

    def get_database_url(self) -> str:
        """
        Constructs or returns the database URL.
        If DATABASE_URL is explicitly set, it's used. Otherwise, it's built
        from individual POSTGRES_* components.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings object.
    The @lru_cache decorator ensures that the Settings object is created only once.
    """
    return Settings()

# Global settings instance to be imported by other modules
settings = get_settings()
