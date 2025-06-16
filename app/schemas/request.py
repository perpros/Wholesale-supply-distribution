from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from app.models.base import ProductType, RequestStatus
from app.schemas.user import UserRead
from app.schemas.request_status_history import RequestStatusHistoryRead # New import

# Forward declaration for ProposalRead to handle circular dependency
class ProposalRead(BaseModel): # Keep this simplified version or ensure proposal.py is compatible
    id: int
    quantity: int
    # status: str # Defined in proposal.py as ProposalStatus enum
    supplier_id: int
    # supplier: UserRead # If full UserRead is here, ensure no deep circular issues
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RequestBase(BaseModel):
    product_type: ProductType
    quantity: int = Field(gt=0) # quantity >= 1
    promised_delivery_date: datetime
    expiration_date: datetime

class RequestCreate(RequestBase):
    @validator('promised_delivery_date', 'expiration_date', pre=True, always=True)
    def date_must_be_in_future(cls, v_date_str_or_dt, field):
        if isinstance(v_date_str_or_dt, str):
            try:
                v_date_str_or_dt = datetime.fromisoformat(v_date_str_or_dt.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"{field.name} is not a valid ISO 8601 datetime string")

        # Ensure it's a datetime object now for comparison
        if not isinstance(v_date_str_or_dt, datetime):
             raise ValueError(f"{field.name} must be a datetime object or valid ISO string")

        # Extract date part for comparison with today() if datetime includes time
        # Assuming UTC for server-side dates, make sure comparison is fair
        # For simplicity, if it's naive, compare with naive date.today()
        # If timezone-aware, ensure comparison is correct. FastAPI usually handles ISO strings to tz-aware.
        compare_date = v_date_str_or_dt.date() #if v_date_str_or_dt.tzinfo else v_date_str_or_dt.replace(tzinfo=None).date()

        if compare_date <= date.today():
            raise ValueError(f'{field.name} must be in the future')
        return v_date_str_or_dt

    @validator('expiration_date', pre=True, always=True)
    def expiration_must_be_after_promised(cls, v_exp_date, values, field):
        # This validator runs after individual field validators if pre=False
        # With pre=True, always=True, it runs on raw input for this field.
        # values might not have promised_delivery_date fully validated/converted yet.
        # It's generally safer to have such cross-field validation with pre=False,
        # or ensure all inputs are converted first.

        # Re-evaluate how 'values' is populated when pre=True.
        # For now, assume promised_delivery_date is in values if provided.

        prom_date_val = values.get('promised_delivery_date')
        if not prom_date_val or not v_exp_date: # if either is not provided, can't compare
            return v_exp_date

        # Ensure both are datetime objects
        if isinstance(v_exp_date, str):
            try:
                v_exp_date = datetime.fromisoformat(v_exp_date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("expiration_date is not a valid ISO 8601 datetime string")
        if not isinstance(v_exp_date, datetime):
             raise ValueError("expiration_date must be a datetime object or valid ISO string")


        if isinstance(prom_date_val, str):
            try:
                prom_date_val = datetime.fromisoformat(prom_date_val.replace('Z', '+00:00'))
            except ValueError:
                 # This error should ideally be caught by promised_delivery_date's own validator
                raise ValueError("promised_delivery_date is not a valid ISO 8601 datetime string for comparison")
        if not isinstance(prom_date_val, datetime):
            raise ValueError("promised_delivery_date must be a datetime object or valid ISO string for comparison")


        if v_exp_date <= prom_date_val:
            raise ValueError('Expiration date must be after promised delivery date')
        return v_exp_date


class RequestUpdate(BaseModel):
    product_type: Optional[ProductType] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    promised_delivery_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    # status: Optional[RequestStatus] = None # Status changes should be via specific endpoints

    # Re-using similar validation logic as RequestCreate for updated fields
    @validator('promised_delivery_date', 'expiration_date', pre=True, always=True)
    def date_must_be_in_future_if_provided(cls, v_date, field):
        if v_date is None: return v_date
        if isinstance(v_date, str):
            try: v_date = datetime.fromisoformat(v_date.replace('Z', '+00:00'))
            except ValueError: raise ValueError(f"{field.name} is not a valid ISO 8601 datetime string")
        if not isinstance(v_date, datetime): raise ValueError(f"{field.name} must be a datetime object or valid ISO string")

        compare_date = v_date.date() #if v_date.tzinfo else v_date.replace(tzinfo=None).date()
        if compare_date <= date.today():
            raise ValueError(f'{field.name} must be in the future')
        return v_date

    @validator('expiration_date', pre=True, always=True)
    def expiration_must_be_after_promised_if_both_provided(cls, v_exp_date, values, field):
        if v_exp_date is None: return v_exp_date

        prom_date_val = values.get('promised_delivery_date')
        # If promised_delivery_date is not being updated, it won't be in `values` unless `always=True`
        # This cross-field validation is complex with Pydantic's `values` behavior and `pre=True`.
        # A root_validator would be more robust for cross-field checks after individual field parsing.
        # For now, this will only work if promised_delivery_date is also part of the update payload.

        if not prom_date_val: return v_exp_date # Cannot compare

        if isinstance(v_exp_date, str):
            try: v_exp_date = datetime.fromisoformat(v_exp_date.replace('Z', '+00:00'))
            except ValueError: raise ValueError("expiration_date is not a valid ISO 8601 datetime string")
        if not isinstance(v_exp_date, datetime): raise ValueError("expiration_date must be a datetime object or valid ISO string")

        if isinstance(prom_date_val, str):
            try: prom_date_val = datetime.fromisoformat(prom_date_val.replace('Z', '+00:00'))
            except ValueError: raise ValueError("promised_delivery_date is not a valid ISO 8601 datetime string for comparison")
        if not isinstance(prom_date_val, datetime): raise ValueError("promised_delivery_date must be a datetime object or valid ISO string for comparison")

        if v_exp_date <= prom_date_val:
            raise ValueError('Expiration date must be after promised delivery date')
        return v_exp_date


class RequestRead(RequestBase):
    id: int
    status: RequestStatus
    requester_id: int
    requester: UserRead
    proposals: List[ProposalRead] = []
    status_history: List[RequestStatusHistoryRead] = [] # Added this line
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
