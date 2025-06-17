from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, requests, proposals

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(requests.router, prefix="/requests", tags=["Requests"])
api_router.include_router(proposals.router, prefix="/proposals", tags=["Proposals"])
