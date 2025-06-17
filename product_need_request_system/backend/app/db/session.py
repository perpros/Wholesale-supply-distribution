"""
Database session management.

This module provides the SQLAlchemy engine, a session factory (SessionLocal),
and a dependency (get_db) for FastAPI routes to obtain a database session.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Import the settings from core.config

# Create the SQLAlchemy engine using the database URL from settings
# pool_pre_ping=True enables a check to ensure connections are alive before use
engine = create_engine(settings.get_database_url(), pool_pre_ping=True)

# Create a configured "Session" class
# autocommit=False and autoflush=False are common defaults for FastAPI applications
# to allow for manual control over transaction commits and flushes within route handlers.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI dependency to get a database session.

    Yields a SQLAlchemy session that is automatically closed after the request.
    Ensures database connections are properly managed and released.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
