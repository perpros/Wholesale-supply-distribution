from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.token import Token
from app.core.security import create_access_token, verify_password
from app.services.user_service import user_service # Use the instance
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from datetime import timedelta

router = APIRouter(prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = user_service.get_user_by_email(db, email=form_data.username) # username is email
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value}, # Store email and role in token
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
