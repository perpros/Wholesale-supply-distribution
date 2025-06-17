"""
Main API router for version 1 of the application.

Aggregates all endpoint routers for the /api/v1 path.
"""
from fastapi import APIRouter

# Import endpoint modules
from .endpoints import login
from .endpoints import users
from .endpoints import requests
from .endpoints import proposals # Added import for proposals router

api_router = APIRouter()

# Include routers from endpoint modules
api_router.include_router(login.router, tags=["Login & Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["Proposals"]) # Added proposals router

# Example of including other routers for different resources:
# from .endpoints import items
# api_router.include_router(items.router, prefix="/items", tags=["Items"])

# This api_router will be included in the main FastAPI app instance in backend/main.py
# with a prefix like /api/v1.
