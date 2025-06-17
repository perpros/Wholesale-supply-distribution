from pydantic import BaseModel, Field
from typing import Optional, List # Keep List
from datetime import date
from backend.app.models.enums import ProductType, RequestStatus
# Forward references will be used for User and Proposal schemas
# from .user import User # Causes circular import if User imports Request
# from .proposal import Proposal # Causes circular import if Proposal imports Request

class RequestBase(BaseModel):
    product_type: ProductType
    quantity: int = Field(..., gt=0)
    promised_delivery_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[RequestStatus] = RequestStatus.SUBMITTED

class RequestCreate(RequestBase):
    pass

class RequestUpdate(BaseModel):
    product_type: Optional[ProductType] = None
    quantity: Optional[int] = Field(None, gt=0)
    promised_delivery_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[RequestStatus] = None

class Request(RequestBase): # For response
    id: int
    owner_id: int
    owner: Optional["User"] = None      # Forward reference to User schema
    proposals: List["Proposal"] = []  # Forward reference to list of Proposal schemas
    # status_history: List["RequestStatusHistory"] = [] # If you want to show this too

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

# Import schemas needed for forward reference resolution
from .user import User # User schema should be defined in user.py
from .proposal import Proposal # Proposal schema should be defined in proposal.py
# from .request_status_history import RequestStatusHistory # If used

Request.model_rebuild() # Update forward references
