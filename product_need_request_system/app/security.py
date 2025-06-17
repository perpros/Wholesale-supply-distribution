from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import crud, models, schemas # models for User model, schemas for UserRole
from .database import get_db

# Password Hashing Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# JWT Settings
SECRET_KEY = "your-super-secret-key-for-dev-only"  # Replace with env variable in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Default expiry: 30 minutes

# This URL must match the endpoint where tokens are issued (the login route)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
        # token_data = schemas.TokenData(email=email) # If you had a TokenData schema
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# Optional: If you add an `is_active` field to your User model
# def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
#     if not current_user.is_active: # Assuming User model has is_active field
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
#     return current_user

# Role-specific dependencies
def require_role(required_role: schemas.UserRole):
    """
    Dependency that checks if the current user has the required role.
    """
    def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
        # current_user.role is SQLAlchemy enum object from model, compare its .value
        # or ensure comparison is between two schemas.UserRole enum members
        # If current_user.role is already a schemas.UserRole enum (e.g. after Pydantic validation), direct comparison is fine.
        # Given current_user is models.User, its .role is likely the DB enum type.
        # We need to ensure this comparison is robust.
        # Assuming models.User.role is a string or an enum compatible with schemas.UserRole.value

        # Correct comparison: current_user.role is the DB model's enum (e.g. UserRoleEnum defined in models.py)
        # required_role is schemas.UserRole
        # So, compare current_user.role.value with required_role.value

        user_role_value = current_user.role # This should be the string value from the DB if mapped correctly by SA
        if isinstance(current_user.role, Enum): # If it's an Enum object from SA
            user_role_value = current_user.role.value

        if user_role_value != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User with role '{user_role_value}' does not have access. Required role: '{required_role.value}'"
            )
        return current_user
    return role_checker

# Specific role requirement dependencies
require_admin = require_role(schemas.UserRole.ADMIN)
require_supplier = require_role(schemas.UserRole.SUPPLIER)
require_end_user = require_role(schemas.UserRole.END_USER)


# A more flexible alternative for checking multiple roles (if needed later)
# def require_roles(required_roles: List[schemas.UserRole]):
#     def role_checker(current_user: models.User = Depends(get_current_user)) -> models.User:
#         user_role_value = current_user.role
#         if isinstance(current_user.role, Enum):
#             user_role_value = current_user.role.value
#
#         if user_role_value not in [role.value for role in required_roles]:
#             raise HTTPException(...)
#         return current_user
#     return role_checker
from enum import Enum # Add this at the top of the file if not already there.
