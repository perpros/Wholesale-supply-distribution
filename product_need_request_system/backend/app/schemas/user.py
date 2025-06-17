"""
Pydantic Schemas for User data.

Defines various schemas for creating, updating, reading, and storing user information.
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional

# Forward references or actual imports for Role schemas will be handled
# once Role CRUD and full schema definitions are in place.
# For now, roles might be represented as simple lists or omitted in user output schemas.

class UserBase(BaseModel):
    """
    Base schema for user attributes.
    Shared by UserCreate, UserUpdate, and UserInDBBase.
    """
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Inherits from UserBase and adds the password field.
    """
    password: str

class UserUpdate(UserBase):
    """
    Schema for updating an existing user.
    All fields are optional, including the password.
    """
    email: Optional[EmailStr] = None # Allow email updates if needed
    password: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDBBase(UserBase):
    """
    Base schema for user data as stored in the database.
    Includes the user ID and prepares for ORM interaction.
    """
    id: int
    # roles: List[str] = [] # Placeholder for roles, to be refined with RoleSchema

    class Config:
        """
        Pydantic configuration for ORM mode.
        Allows the model to be populated from ORM objects.
        Pydantic v2 uses `from_attributes = True`.
        """
        from_attributes = True

class User(UserInDBBase):
    """
    Schema for returning user data in API responses.
    This is typically what's sent to the client (without sensitive data like hashed_password).
    """
    # Add any additional fields specific to API output if different from UserInDBBase
    pass

class UserInDB(UserInDBBase):
    """
    Schema representing a user object as it is stored in the database,
    including the hashed password. This should not be returned in API responses.
    """
    hashed_password: str
