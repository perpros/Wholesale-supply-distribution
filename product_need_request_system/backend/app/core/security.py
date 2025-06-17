"""
Security utilities for password hashing, JWT creation, and token decoding.

Provides functions for:
- Creating JWT access tokens.
- Verifying plain passwords against hashed passwords.
- Hashing plain passwords.
- Decoding JWT access tokens to extract token data.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Union, List # Added List

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.schemas.token import TokenData

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings from application configuration
ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(
    subject: Union[str, Any], roles: List[str] = [], expires_delta: timedelta | None = None
) -> str:
    """
    Creates a new JWT access token.

    Args:
        subject: The subject of the token (e.g., user ID or email).
        roles: A list of role names to include in the token.
        expires_delta: Optional timedelta to specify token expiry.
                       If None, uses ACCESS_TOKEN_EXPIRE_MINUTES from settings.

    Returns:
        The encoded JWT access token as a string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "roles": roles} # Added roles to the payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password: The plain text password.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password as a string.
    """
    return pwd_context.hash(password)

def decode_access_token(token: str) -> TokenData | None:
    """
    Decodes a JWT access token and returns its data.

    Args:
        token: The JWT access token to decode.

    Returns:
        TokenData object if the token is valid and contains a subject,
        None otherwise.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        roles: List[str] = payload.get("roles", []) # Extract roles, default to empty list
        if username is None:
            return None
        token_data = TokenData(username=username, roles=roles) # Include roles in TokenData
    except JWTError:
        return None
    return token_data
