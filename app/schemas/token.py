from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    # sub: Optional[str] = None # 'sub' is often used for subject (user id or email)
