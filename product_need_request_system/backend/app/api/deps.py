"""
FastAPI Dependencies for API endpoints.

This module provides reusable dependencies for:
- Obtaining a database session (`get_db`).
- Authenticating users via OAuth2 tokens (`get_current_user_from_token`,
  `get_current_user_model`, `get_current_active_user`).
- Role-based access control (`RoleChecker`).
"""
from typing import List, Generator, Set

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
# jose.JWTError is not directly used here but good to know it's related
# from jose import JWTError

from app.core.config import settings
from app.core.security import decode_access_token
from app.crud.crud_user import user as crud_user # Renamed to avoid conflict
from app.models.user import User as UserModel # UserModel is the SQLAlchemy model
from app.schemas.token import TokenData
from app.db.session import SessionLocal # Import SessionLocal for get_db

# OAuth2PasswordBearer scheme for token-based authentication.
# tokenUrl points to the endpoint where clients can obtain a token.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get a database session.
    Yields a SQLAlchemy session that is automatically closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_from_token(
    token: str = Depends(reusable_oauth2)
) -> TokenData:
    """
    Dependency to decode and validate an access token, returning its data.
    Raises HTTPException if the token is invalid or the username is missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if not token_data or not token_data.username: # Check for username specifically
        raise credentials_exception
    return token_data

def get_current_user_model(
    db: Session = Depends(get_db),
    token_data: TokenData = Depends(get_current_user_from_token)
) -> UserModel:
    """
    Dependency to get the current user as a SQLAlchemy model instance.
    Fetches the user from the database based on the username in the token data.
    Raises HTTPException if the user is not found.
    This now relies on crud_user.get_by_email to potentially load roles.
    """
    user_model = crud_user.get_by_email(db, email=token_data.username)
    if not user_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_model

def get_current_active_user(
    current_user: UserModel = Depends(get_current_user_model),
) -> UserModel:
    """
    Dependency to get the current active user.
    Checks if the user model obtained from `get_current_user_model` is active.
    Raises HTTPException if the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

class RoleChecker:
    """
    Dependency class for Role-Based Access Control (RBAC).
    Checks if the current active user has at least one of the allowed roles.
    """
    def __init__(self, allowed_roles: List[str]):
        """
        Args:
            allowed_roles: A list of role names that are permitted to access the endpoint.
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserModel = Depends(get_current_active_user)):
        """
        Callable part of the dependency.
        Verifies user roles against allowed_roles.

        Args:
            current_user: The currently authenticated and active user model,
                          expected to have roles populated (e.g., via eager loading).

        Raises:
            HTTPException (403 Forbidden) if the user does not have any of the allowed roles.
        """
        # Ensure roles are loaded for the user. This depends on get_by_email in crud_user
        # using joinedload or similar to populate current_user.roles.
        if not hasattr(current_user, 'roles') or not current_user.roles:
            user_roles_set: Set[str] = set()
        else:
            user_roles_set = {role.name for role in current_user.roles if role.name}


        if not any(role_name in user_roles_set for role_name in self.allowed_roles):
            required_roles_str = ", ".join(self.allowed_roles)
            user_roles_str = ", ".join(list(user_roles_set)) if user_roles_set else "none"

            detail_msg = (
                f"User does not have the required role(s): '{required_roles_str}'. "
                f"User's roles: '{user_roles_str}'."
            )
            if not user_roles_set:
                 detail_msg = (
                    f"User has no assigned roles. Required role(s): '{required_roles_str}'."
                 )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detail_msg
            )
        return current_user

# Example usage for an endpoint:
# @router.get("/admin-only", dependencies=[Depends(RoleChecker(["admin"]))])
# async def get_admin_data(...):
#     return {"message": "Admin data"}
