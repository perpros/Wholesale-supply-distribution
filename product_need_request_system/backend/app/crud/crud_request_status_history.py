"""
CRUD operations for RequestStatusHistory model.
"""
from sqlalchemy.orm import Session # Session is typically used in method signatures, not globally here

from app.crud.base import CRUDBase
from app.models.request_status_history import RequestStatusHistory as RequestStatusHistoryModel
from app.schemas.request_status_history import RequestStatusHistoryCreate
# Assuming RequestStatusHistoryUpdate is not significantly different from Create for now.
# If it is, it should be defined in schemas.request_status_history.

class RequestStatusHistoryUpdate(RequestStatusHistoryCreate): # Placeholder if needed
    """
    Schema for updating a request status history entry.
    Currently assumes the same fields as creation. In many cases, history entries are immutable.
    """
    pass

class CRUDRequestStatusHistory(CRUDBase[RequestStatusHistoryModel, RequestStatusHistoryCreate, RequestStatusHistoryUpdate]):
    """
    CRUD operations for RequestStatusHistory.
    Inherits basic Create, Read, Update, Delete from CRUDBase.
    Specific methods can be added here if needed (e.g., get_history_for_request).
    """
    # No specific methods needed beyond CRUDBase for now, as history entries are usually simple.
    # Create is handled by CRUDBase. Updates/Deletes of history are generally not done.
    # Reading history will likely be part of fetching a Request and its related history entries.
    pass

request_status_history = CRUDRequestStatusHistory(RequestStatusHistoryModel)
