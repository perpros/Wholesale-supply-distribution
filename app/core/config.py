from pydantic import BaseSettings # Make sure this is BaseSettings for Pydantic v1/v2 compatibility
import os

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = "mysql+mysqlclient://user:password@localhost/dbname"
    API_V1_STR: str = "/api/v1" # Added API version string

    class Config:
        env_file = ".env"

settings = Settings()
