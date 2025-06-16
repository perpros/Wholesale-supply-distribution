from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
# To avoid circular import with services directly using models/schemas,
# we might need to pass db to a service function or import service carefully.
# For get_current_user, it needs user_service.
from app.services.user_service import user_service
from app.models.user import User as UserModel # Renamed to avoid clash if User schema is also User
from app.schemas.token import TokenData # For completeness, though sub is used directly


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    email: str | None = payload.get("sub") # 'sub' typically holds the username (email in our case)
    if email is None:
        raise credentials_exception

    # Validate with TokenData schema if needed, for example, if token has more fields
    # token_data = TokenData(email=email_from_sub)

    user = user_service.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception # Or a more specific "User not found"
    return user

# Example of a dependency for active users, if you add an 'is_active' field to your User model
# async def get_current_active_user(
#     current_user: UserModel = Depends(get_current_user)
# ) -> UserModel:
#     if not current_user.is_active:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
#     return current_user
