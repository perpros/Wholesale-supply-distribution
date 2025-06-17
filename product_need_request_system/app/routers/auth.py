from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas # schemas for Token response
from app.security import verify_password, create_access_token # security functions
from app.database import get_db

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # The 'sub' (subject) of the token is usually the user's unique identifier.
    # Using email here as per security.py's get_current_user logic.
    access_token_data = {"sub": user.email}
    access_token = create_access_token(data=access_token_data)

    return {"access_token": access_token, "token_type": "bearer"}
