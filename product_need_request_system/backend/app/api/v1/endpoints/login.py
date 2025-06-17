"""
API Endpoints for user login and token management.

Provides endpoints for:
- Obtaining an OAuth2 compatible access token.
- Testing the validity of an access token.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Standard form for username/password
from sqlalchemy.orm import Session

from app import crud # Accesses crud.user
from app import schemas # Accesses schemas.Token, schemas.User
from app.api import deps # Contains dependencies like get_db, get_current_active_user
from app.core import security # For create_access_token
from app.core.config import settings
from app.models.user import User as UserModel # For type hinting current_user

router = APIRouter()

@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends() # Uses 'username' and 'password' fields
) -> Any:
    """
    OAuth2 compatible token login.

    Authenticates a user based on email (passed as 'username' in form_data) and password.
    Returns an access token if authentication is successful.
    """
    user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for 401
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # Extract role names from the user's roles relationship
    # This relies on user.roles being populated (e.g., by joinedload in crud.user.get_by_email)
    user_roles = [role.name for role in user.roles if role.name] if user.roles else []

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.email,  # Using email as the subject in the JWT
        roles=user_roles,    # Pass the list of role names
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer", # Standard token type
    }

@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: UserModel = Depends(deps.get_current_active_user)) -> Any:
    """
    Test access token endpoint.

    Requires a valid access token. Returns the authenticated user's data
    (excluding sensitive information like hashed_password, as defined by schemas.User).
    """
    return current_user

# Example of a protected endpoint using RoleChecker:
# @router.get("/users/me/items", dependencies=[Depends(deps.RoleChecker(["user", "admin"]))])
# async def read_own_items(current_user: UserModel = Depends(deps.get_current_active_user)):
#     # This endpoint would only be accessible to users with "user" or "admin" roles.
#     return [{"item_id": "Foo", "owner": current_user.email}]
