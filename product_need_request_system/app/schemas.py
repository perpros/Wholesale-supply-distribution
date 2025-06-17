from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

# Re-define Enums from models.py for API schema clarity and potential distinct API representation
# These should ideally be kept in sync with models.UserRole and models.RequestStatus

class UserRole(str, Enum):
    END_USER = "EndUser"
    SUPPLIER = "Supplier"
    ADMIN = "Admin"

class RequestStatus(str, Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RESUBMITTED = "resubmitted"
    EXPIRED = "expired"
    CLOSED = "closed"

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}

class User(UserInDBBase):
    pass # For now, same as UserInDBBase

class UserInDB(UserInDBBase):
    hashed_password: str


# --- Request Schemas ---
class RequestBase(BaseModel):
    product_type: str
    quantity: int
    promised_delivery_date: date
    expiration_date: date

class RequestCreate(RequestBase):
    @field_validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

    @field_validator('promised_delivery_date')
    def promised_date_must_be_future(cls, v):
        if v <= date.today():
            raise ValueError('Promised delivery date must be in the future')
        return v

    @field_validator('expiration_date')
    def expiration_date_must_be_future_and_after_promised(cls, v, values):
        # Pydantic v2: values.data contains the raw data
        # It seems there's a slight change in how values are accessed in v2 for cross-field validation.
        # The `values` argument to a validator is a `ValidationInfo` object.
        # The actual data for other fields is in `values.data`.

        # Ensure promised_delivery_date is present before comparison
        promised_delivery_date = values.data.get('promised_delivery_date')

        if promised_delivery_date and v <= promised_delivery_date:
            raise ValueError('Expiration date must be after promised delivery date')
        if v <= date.today():
            raise ValueError('Expiration date must be in the future')
        return v

class RequestUpdate(BaseModel):
    product_type: Optional[str] = None
    quantity: Optional[int] = None
    promised_delivery_date: Optional[date] = None
    expiration_date: Optional[date] = None
    # Status updates are typically handled by specific actions/endpoints, not general update
    # status: Optional[RequestStatus] = None

    @field_validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

    @field_validator('promised_delivery_date')
    def promised_date_must_be_future(cls, v: Optional[date]):
        if v is not None and v <= date.today():
            raise ValueError('Promised delivery date must be in the future')
        return v

    @field_validator('expiration_date')
    def expiration_date_must_be_future_and_after_promised(cls, v: Optional[date], values):
        if v is None:
            return v # Nothing to validate if not provided

        promised_delivery_date = values.data.get('promised_delivery_date')

        # If promised_delivery_date is not being updated, we might need to fetch it
        # or rely on the existing model state if this validator is part of a more complex update logic.
        # For simple Pydantic validation, we only check if it's present in the current update payload.
        if promised_delivery_date and v <= promised_delivery_date:
            raise ValueError('Expiration date must be after promised delivery date')

        if v <= date.today():
            raise ValueError('Expiration date must be in the future')
        return v

class RequestInDBBase(RequestBase):
    id: int
    user_id: int
    status: RequestStatus
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class Request(RequestInDBBase):
    user: User # Nested user information for response

# --- Proposal Schemas ---
class ProposalBase(BaseModel):
    # request_id: int # request_id will be path parameter for creation in many REST designs
    quantity: int

class ProposalCreate(ProposalBase):
    request_id: int # Explicitly add request_id for creation, as it's part of the model
    @field_validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

class ProposalUpdate(BaseModel):
    quantity: Optional[int] = None
    @field_validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError('Quantity must be at least 1')
        return v

class ProposalInDBBase(ProposalBase):
    id: int
    supplier_id: int
    request_id: int # Added back for response model consistency
    submitted_at: datetime
    model_config = {"from_attributes": True}

class Proposal(ProposalInDBBase):
    supplier: User # Nested supplier information

# --- RequestStatusHistory Schemas ---
class RequestStatusHistoryBase(BaseModel):
    request_id: int
    status: RequestStatus
    # changed_by_user_id: Optional[int] = None # This will be set by the system/auth user

class RequestStatusHistoryCreate(RequestStatusHistoryBase):
    pass # changed_by_user_id will be set based on the authenticated user or system

class RequestStatusHistory(RequestStatusHistoryBase):
    id: int
    changed_at: datetime
    changed_by_user_id: Optional[int] = None # Include for response
    model_config = {"from_attributes": True}

# --- Notification Schemas ---
class NotificationBase(BaseModel):
    request_id: int # Which request this notification pertains to
    message: str

class NotificationCreate(NotificationBase):
    user_id: int # Who should receive this notification

class Notification(NotificationBase):
    id: int
    user_id: int # Include user_id in response
    created_at: datetime
    read: bool
    model_config = {"from_attributes": True}

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
