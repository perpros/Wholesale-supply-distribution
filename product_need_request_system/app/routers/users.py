from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.database import get_db
from app.security import get_current_user, require_admin # Import new security dependencies

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

# User registration - public endpoint
@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    created_user = crud.create_user(db=db, user=user) # Uses security.get_password_hash
    return created_user

# Get current user (self)
@router.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    # FastAPI will automatically convert models.User to schemas.User for response
    return current_user

# Admin: List all users
@router.get("/", response_model=List[schemas.User], dependencies=[Depends(require_admin)])
def read_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # current_admin: models.User = Depends(require_admin) # Alternative: per-endpoint dependency
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

# Admin: Get specific user by ID
@router.get("/{user_id}", response_model=schemas.User, dependencies=[Depends(require_admin)])
def read_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    # current_admin: models.User = Depends(require_admin) # Alternative
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user
