from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import Generator

# Construct the database URL (example for PostgreSQL)
# In a real app, ensure POSTGRES_USER, POSTGRES_PASSWORD, etc. are set in config or .env
if not settings.SQLALCHEMY_DATABASE_URI:
    settings.SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
