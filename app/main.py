from fastapi import FastAPI
from app.api.routers import auth
from app.api.routers import users
from app.api.routers import requests
from app.api.routers import proposals
from app.core.config import settings

app = FastAPI(title="Product Need Request System")

# Include API v1 routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(proposals.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Product Need Request System API"}
