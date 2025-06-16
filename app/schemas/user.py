from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.base import UserRole # Assuming enums are accessible here

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(min_length=8)
    role: UserRole

class UserUpdate(UserBase):
    password: Optional[str] = Field(default=None, min_length=8)
    full_name: Optional[str] = None
    role: Optional[UserRole] = None

class UserRead(UserBase):
    id: int
    role: UserRole
    created_at: datetime
    is_active: bool = True # Assuming users can be active/inactive

    class Config:
        from_attributes = True # Replaces orm_mode = True in Pydantic v2
