"""
Pydantic Schemas for Role data.

Defines schemas for creating and representing roles.
"""
from pydantic import BaseModel
from typing import Optional

class RoleBase(BaseModel):
    """
    Base schema for role attributes.
    """
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """
    Schema for creating a new role.
    Inherits all attributes from RoleBase.
    """
    pass

class Role(RoleBase):
    """
    Schema for representing a role, including its ID.
    This is typically used when returning role data from the API.
    """
    id: int

    class Config:
        """
        Pydantic configuration for ORM mode.
        Allows the model to be populated from ORM objects.
        Pydantic v2 uses `from_attributes = True`.
        """
        from_attributes = True
