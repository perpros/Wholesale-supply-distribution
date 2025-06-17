from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    # Add other relevant fields that you might store in the token, e.g., user_id, roles
    # For now, keeping it simple with email.
