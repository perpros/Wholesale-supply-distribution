from fastapi import FastAPI
from backend.app.api.v1.api import api_router as v1_api_router # Import the main v1 router

app = FastAPI(title="Wholesale Supply Distribution API")

# Include the main v1 router
app.include_router(v1_api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Wholesale Supply Distribution API - Root"}

# Placeholder for startup events, e.g. creating initial DB data
# @app.on_event("startup")
# async def startup_event():
#     pass
