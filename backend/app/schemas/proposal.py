from pydantic import BaseModel, Field
from typing import Optional, List # Added List for consistency, though not strictly needed here yet
from backend.app.models.enums import ProposalStatus
# Forward references for User and Request schemas
# from .user import User
# from .request import Request

class ProposalBase(BaseModel):
    quantity_proposed: int = Field(..., gt=0)
    # Add other fields like price, comments, etc.
    status: Optional[ProposalStatus] = ProposalStatus.SUBMITTED

class ProposalCreate(ProposalBase):
    request_id: int # Required when creating a proposal

class ProposalUpdate(BaseModel):
    quantity_proposed: Optional[int] = Field(None, gt=0)
    status: Optional[ProposalStatus] = None
    # Add other updatable fields

class Proposal(ProposalBase): # For response
    id: int
    request_id: int
    supplier_id: int
    request: Optional["Request"] = None    # Forward reference to Request schema
    supplier: Optional["User"] = None     # Forward reference to User schema

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

# Import schemas needed for forward reference resolution
from .user import User
from .request import Request

Proposal.model_rebuild() # Update forward references
