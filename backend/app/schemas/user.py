from pydantic import BaseModel, EmailStr
from typing import Optional, List
# Forward references for Request and Proposal schemas
# from .request import Request  # This would be a circular import if Request imports User
# from .proposal import Proposal # Same here

# Schema for user creation (input)
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user" # Default role

# Schema for user representation (output, usually without password)
class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    requests: List["Request"] = []  # Assuming Request schema will be defined
    proposals: List["Proposal"] = [] # Assuming Proposal schema will be defined
    # status_changes: List["RequestStatusHistory"] = [] # If you want to show these too

    class Config:
        from_attributes = True

# Forward references need to be updated after all models are defined in this module
# or by importing them if not creating circular dependencies.
# For now, relying on Pydantic's string evaluation for forward refs.
# If Request and Proposal schemas are in different files, ensure they are loaded.

# To resolve forward references, you would typically do this at the end of the file
# if all referenced models are defined within this file or imported:
# User.model_rebuild()
# However, for cross-file references, Pydantic usually handles it if the modules are imported,
# or you might need a central place to call model_rebuild once all schemas are defined.

# For now, we will add model_rebuild() at the end of each schema file that uses forward refs.
# This requires importing the referenced schemas.

from .request import Request # This will be defined soon
from .proposal import Proposal # This will be defined soon
# from .request_status_history import RequestStatusHistory # If used

User.model_rebuild() # Pydantic v2 way to update forward refs
