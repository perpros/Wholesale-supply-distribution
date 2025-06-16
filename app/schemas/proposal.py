from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.base import ProposalStatus
from app.schemas.user import UserRead # For nesting supplier info
# from app.schemas.request import RequestRead # This would be a full circular dependency

# To handle circular dependency with RequestRead, we can use a forward reference
# or define a simpler schema for the request if full details are not needed here.
# For now, let's assume we only need the request_id or a simplified RequestInProposalRead schema.

class RequestBasicRead(BaseModel): # A simplified Request schema for nesting in ProposalRead
    id: int
    product_type: str # Using str representation of enum for simplicity here
    status: str

    class Config:
        from_attributes = True

class ProposalBase(BaseModel):
    quantity: int = Field(gt=0) # quantity >= 1
    # unit_price: Optional[float] = Field(default=None, gt=0)
    # comments: Optional[str] = None

class ProposalCreate(ProposalBase):
    pass # No extra fields for creation beyond base for now

class ProposalUpdate(BaseModel):
    quantity: Optional[int] = Field(default=None, gt=0)
    # unit_price: Optional[float] = Field(default=None, gt=0)
    # comments: Optional[str] = None
    status: Optional[ProposalStatus] = None # If status can be updated directly

class ProposalRead(ProposalBase):
    id: int
    status: ProposalStatus # Use the enum here
    request_id: int
    # request: RequestBasicRead # Nested basic request info
    supplier_id: int
    supplier: UserRead # Nested supplier information
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Now, update RequestRead in app/schemas/request.py to use this fully defined ProposalRead
# This is tricky with shell script. The ideal way is to use Python's update_forward_refs()
# For now, the forward declaration in request.py is a common pattern.
# The subtask environment might not allow re-writing parts of files easily.
# We will rely on FastAPI/Pydantic's ability to resolve these at runtime.
