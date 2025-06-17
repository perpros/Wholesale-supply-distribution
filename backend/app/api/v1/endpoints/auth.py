from typing import Annotated, Optional # Added Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta # Added timedelta

from backend.app.schemas.token import Token
from backend.app.security import jwt, hashing
from backend.app.crud import user as crud_user
from backend.app.models.user import User as UserModel
from backend.app.database import get_db
from backend.app.core.config import settings # Added settings

router = APIRouter()

# Helper function to authenticate user
def authenticate_user(db: Session, email: str, password: str) -> Optional[UserModel]: # UserModel type hint
    user = crud_user.user.get_by_email(db, email=email)
    if not user:
        return None
    if not Hasher.verify_password(password, user.hashed_password):
        return None
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Subject of the token can be user's email or ID. Email is often simpler.
    # If using ID, ensure it's stored as string if needed by downstream systems.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example: Endpoint to create a user (useful for initial setup or admin interfaces)
# from backend.app.schemas.user import UserCreate, User as UserSchema
# @router.post("/users/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
# def create_user_endpoint(
#     *,
#     db: Annotated[Session, Depends(get_db)],
#     user_in: UserCreate
# ):
#     existing_user = crud_user.user.get_by_email(db, email=user_in.email)
#     if existing_user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Email already registered",
#         )
#     new_user = crud_user.user.create(db, obj_in=user_in)
#     return new_user
