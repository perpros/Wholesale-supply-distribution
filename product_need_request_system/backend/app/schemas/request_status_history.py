"""
Pydantic Schemas for Request Status History.

Defines schemas for creating and representing entries in the request status history log.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.models.enums import RequestStatusEnum # Re-use enum from models
# from .user import User # Optional: For embedding user who made the change

class RequestStatusHistoryBase(BaseModel):
    """
    Base schema for request status history attributes.
    """
    status: RequestStatusEnum
    notes: Optional[str] = None

class RequestStatusHistoryCreate(RequestStatusHistoryBase):
    """
    Schema for creating a new request status history entry.
    Requires request_id and allows specifying who changed the status.
    """
    request_id: int
    changed_by_id: Optional[int] = None # Can be None if changed by the system

class RequestStatusHistory(RequestStatusHistoryBase):
    """
    Schema for representing a request status history entry in API responses.
    Includes read-only fields like id, changed_at.
    """
    id: int
    request_id: int
    changed_at: datetime
    changed_by_id: Optional[int] = None

    # changed_by: Optional[User] = None # Optional: Embed User object of who made the change

    class Config:
        """
        Pydantic configuration for ORM mode (from_attributes for Pydantic v2).
        """
        from_attributes = True
