from pydantic import BaseModel
from datetime import datetime
from app.models.base import RequestStatus # Re-using RequestStatus enum

class RequestStatusHistoryBase(BaseModel):
    status: RequestStatus
    # user_id: Optional[int] = None # Could be added if we want to show who triggered the change

class RequestStatusHistoryCreate(RequestStatusHistoryBase):
    request_id: int
    user_id: int | None = None # User who triggered the change, None for system

class RequestStatusHistoryRead(RequestStatusHistoryBase):
    id: int
    request_id: int
    user_id: int | None
    timestamp: datetime

    class Config:
        from_attributes = True
