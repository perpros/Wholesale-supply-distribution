from fastapi import FastAPI
from app.routers import product_need_request_router
from app.db.session import init_db # For initial DB setup
from app.core.config import settings # To access settings if needed

app = FastAPI(
    title="Product Need Request API",
    description="API for managing product need requests.",
    version="0.1.0"
)

# @app.on_event("startup")
# async def on_startup():
#    # This is useful for development to ensure tables are created.
#    # In production, you'd likely use Alembic for migrations.
#    init_db()

app.include_router(
    product_need_request_router,
    prefix="/api/v1", # Added prefix here
    tags=["Product Need Requests"]
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Product Need Request API"}
