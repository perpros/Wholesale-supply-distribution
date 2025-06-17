"""
Pydantic Schemas for Token data.

Defines the structure for JWT tokens and the data they contain.
"""
from pydantic import BaseModel
from typing import List, Optional # Added List and Optional

class Token(BaseModel):
    """
    Schema for the access token response.

    Attributes:
        access_token: The JWT access token.
        token_type: The type of token (e.g., "bearer").
    """
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """
    Schema for the data encoded within an access token.

    Attributes:
        username: The subject of the token, typically the user's email or unique ID.
                  Corresponds to the 'sub' claim in the JWT.
        roles: A list of role names associated with the user.
    """
    username: str | None = None
    roles: List[str] = [] # Added roles field
