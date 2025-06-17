from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List # Added List for consistency
# Forward references for User and Request schemas
# from .user import User
# from .request import Request


class RequestStatusHistoryBase(BaseModel):
    status: str # Storing the string value of the enum
    # request_id and changed_by_id will be path/body params or from context

class RequestStatusHistoryCreate(RequestStatusHistoryBase):
    request_id: int
    # changed_by_id can be automatically set based on current user or system
    pass

class RequestStatusHistory(RequestStatusHistoryBase): # For response
    id: int
    request_id: int
    timestamp: datetime
    changed_by_id: Optional[int] = None
    request: Optional["Request"] = None     # Forward reference to Request schema
    changed_by: Optional["User"] = None    # Forward reference to User schema

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

# Import schemas needed for forward reference resolution
from .user import User
from .request import Request

RequestStatusHistory.model_rebuild() # Update forward references
