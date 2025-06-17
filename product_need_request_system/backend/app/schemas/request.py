"""
Pydantic Schemas for Request data.

Defines schemas for creating, updating, and representing product/service requests.
Includes custom validators for date logic.
"""
from pydantic import BaseModel, validator, Field
from typing import Optional, List
from datetime import datetime, date

from app.models.enums import ProductTypeEnum, RequestStatusEnum
# Assuming User and Proposal schemas are in the same directory (app.schemas)
from .user import User
# from .proposal import Proposal # Uncomment if/when Proposal schema is used here
# from .request_status_history import RequestStatusHistory # For embedding history if needed

class RequestBase(BaseModel):
    """
    Base schema for request attributes.
    """
    product_type: ProductTypeEnum
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")
    promised_delivery_date: date
    expiration_date: date
    # description: Optional[str] = None # Optional field for more details about the request

    @validator('promised_delivery_date')
    def promised_date_must_be_future(cls, v: date) -> date:
        """Validates that promised_delivery_date is in the future."""
        if v <= date.today():
            raise ValueError('Promised delivery date must be in the future')
        return v

    @validator('expiration_date')
    def expiration_date_must_be_after_promised_and_future(cls, v: date, values: dict) -> date:
        """
        Validates that expiration_date is in the future and after promised_delivery_date.
        """
        promised_date = values.get('promised_delivery_date')
        if promised_date and v <= promised_date:
            raise ValueError('Expiration date must be after promised delivery date')
        if v <= date.today(): # Ensures expiration_date itself is also in the future
            raise ValueError('Expiration date must be in the future')
        return v

class RequestCreate(RequestBase):
    """
    Schema for creating a new request. Inherits all fields from RequestBase.
    """
    pass

class RequestUpdate(BaseModel):
    """
    Schema for updating an existing request. All fields are optional.
    Status changes are typically handled by dedicated service/CRUD methods, not direct update.
    """
    product_type: Optional[ProductTypeEnum] = None
    quantity: Optional[int] = Field(None, gt=0, description="Quantity must be greater than 0 if provided")
    promised_delivery_date: Optional[date] = None
    expiration_date: Optional[date] = None
    # description: Optional[str] = None

    # Note: Validators for partial updates can be complex.
    # The following are basic future checks. Cross-field validation (e.g., exp_date > promised_date)
    # during a partial update is better handled in the CRUD/service layer where full object context is available.

    @validator('promised_delivery_date', pre=True, always=True)
    def promised_date_update_must_be_future(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v <= date.today():
            raise ValueError('Promised delivery date must be in the future')
        return v

    @validator('expiration_date', pre=True, always=True)
    def expiration_date_update_must_be_future(cls, v: Optional[date], values: dict) -> Optional[date]:
        if v is not None and v <= date.today():
            raise ValueError('Expiration date must be in the future')

        # Basic cross-validation if promised_delivery_date is also part of the update
        # More robust validation should occur in the CRUD layer with the full existing object.
        # promised_delivery_date_in_update = values.get('promised_delivery_date')
        # if promised_delivery_date_in_update and v and v <= promised_delivery_date_in_update:
        #    raise ValueError('Expiration date must be after promised delivery date')
        return v

class Request(RequestBase):
    """
    Schema for representing a request in API responses.
    Includes additional fields like ID, owner, status, and timestamps.
    """
    id: int
    owner_id: int
    status: RequestStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None

    owner: Optional[User] = None # Embed owner details (User schema defined elsewhere)
    # proposals: List[Proposal] = [] # Optionally embed associated proposals
    # status_history: List[RequestStatusHistory] = [] # Optionally embed status history

    class Config:
        """
        Pydantic configuration for ORM mode (from_attributes for Pydantic v2).
        """
        from_attributes = True
