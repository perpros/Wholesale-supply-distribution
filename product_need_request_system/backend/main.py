"""
Main FastAPI application file.

Initializes the FastAPI application, sets up configurations,
and includes basic health check endpoints.
"""
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text # Required for db.execute(text("SELECT 1"))

from app.core.config import settings
from app.db.session import get_db, engine # Import engine and get_db
from app.api.v1.api import api_router # Import the main API router
# from app.models import Base # Uncomment if you need to create tables (dev only)

# Development-only: Create database tables based on models.
# In a production environment with Alembic, schema migrations are handled by Alembic,
# so this line should be commented out or removed.
# It can be useful for initial local development or certain testing scenarios
# if not using Alembic or wanting a quick start without running migrations.
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="API for managing Product Need Requests and Proposals.",
    version="0.1.0" # Example version
)

@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    For example, check database connectivity or load initial resources.
    """
    print(f"Application '{settings.PROJECT_NAME}' starting up...")
    # Example: Test database connection (optional, as get_db will handle sessions)
    # try:
    #     with engine.connect() as connection:
    #         connection.execute(text("SELECT 1"))
    #     print("Database connection successful on startup.")
    # except Exception as e:
    #     print(f"Database connection failed on startup: {e}")
    #     # Depending on severity, you might want to raise an exception or exit
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    For example, closing database connections or releasing resources.
    """
    print(f"Application '{settings.PROJECT_NAME}' shutting down...")


@app.get("/", summary="Root Health Check", tags=["Health"])
async def root():
    """
    Basic health check endpoint to confirm the API is running.
    Returns the project name and status.
    """
    return {"status": "healthy", "project_name": settings.PROJECT_NAME, "version": app.version}

@app.get("/health", summary="Alternative Health Check", tags=["Health"])
async def health_check():
    """
    An alternative health check endpoint.
    """
    return {"status": "healthy", "message": "API is up and running!"}

@app.get("/db-check", summary="Database Connection Check", tags=["Health"])
async def db_check(db: Session = Depends(get_db)):
    """
    Checks if a database session can be established and a simple query executed.
    This helps verify that the database connection is operational.
    """
    try:
        # Perform a simple query to check DB connectivity
        db.execute(text("SELECT 1"))
        return {"status": "db_healthy", "message": "Database connection successful."}
    except Exception as e:
        # Log the exception here if you have logging setup
        return {"status": "db_unhealthy", "error": str(e)}


# Include the main API router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    # This block allows running the application directly using `python backend/main.py`
    # For development, it's common to use `uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
    print(f"Starting Uvicorn server for {settings.PROJECT_NAME} on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
