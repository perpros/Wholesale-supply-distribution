"""
Pydantic Schemas for Proposal data.

Defines schemas for creating, updating, and representing proposals made by suppliers
in response to requests.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.enums import ProposalStatusEnum # Ensure this path is correct
from .user import User # For embedding supplier information

class ProposalBase(BaseModel):
    """
    Base schema for proposal attributes.
    """
    request_id: int = Field(..., description="The ID of the request this proposal is for.")
    quantity: int = Field(..., gt=0, description="The quantity offered in this proposal; must be greater than 0.")
    # description: Optional[str] = None # Optional: More details about the proposal, e.g., specific terms, product SKU.

class ProposalCreate(ProposalBase):
    """
    Schema for creating a new proposal. Inherits all fields from ProposalBase.
    """
    pass

class ProposalUpdate(BaseModel):
    """
    Schema for updating an existing proposal.
    Currently, only quantity and description might be updatable by the supplier,
    and only if the proposal/request is in a specific state.
    Status updates would likely be handled by separate actions/endpoints.
    """
    quantity: Optional[int] = Field(None, gt=0, description="New quantity; must be greater than 0 if provided.")
    # description: Optional[str] = None

class Proposal(ProposalBase):
    """
    Schema for representing a proposal in API responses.
    Includes read-only fields like ID, supplier details, status, and timestamps.
    """
    id: int
    supplier_id: int
    status: ProposalStatusEnum # Current status of the proposal
    created_at: datetime
    updated_at: Optional[datetime] = None

    supplier: Optional[User] = None # Embed supplier (User) details

    class Config:
        """
        Pydantic configuration for ORM mode (from_attributes for Pydantic v2).
        """
        from_attributes = True
