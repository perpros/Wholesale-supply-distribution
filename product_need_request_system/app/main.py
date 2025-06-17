from fastapi import FastAPI
from app.routers import users, requests, proposals, admin, auth # Import other routers as they are created
# Potentially import database models and engine for create_all if not using Alembic for initial dev
# from app import models
# from app.database import engine

# models.Base.metadata.create_all(bind=engine) # This is for initial table creation without Alembic in dev
                                                # Not recommended if Alembic is fully set up

app = FastAPI(
    title="Product Need Request System",
    description="System for managing product need requests, proposals, lifecycles, supplier interaction, and automated evaluations.",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json", # Standardizing API doc path
    docs_url="/api/v1/docs", # Standardizing API doc path
    redoc_url="/api/v1/redoc" # Standardizing API doc path
)

# Include routers
app.include_router(users.router) # Default prefix is /api/v1/users as defined in users.router
app.include_router(requests.router) # Default prefix is /api/v1/requests as defined in requests.router
app.include_router(proposals.router) # Default prefix is /api/v1/requests/{request_id}/proposals
app.include_router(admin.router) # Default prefix is /api/v1/admin/requests
app.include_router(auth.router) # Default prefix is /api/v1/auth


@app.get("/api/v1/health", tags=["Health"])
async def health_check(): # Changed function name from root to health_check for clarity
    return {"message": "Welcome to the Product Need Request System API"}

# Further configurations: CORS, middleware, exception handlers can be added here
