"""RequestStatusHistory model definition."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base # Adjusted import path
from .enums import RequestStatusEnum

class RequestStatusHistory(Base):
    """
    Logs changes to the status of a Request.

    Attributes:
        id (int): Primary key for the status history entry.
        request_id (int): Foreign key linking to the request whose status changed.
        status (RequestStatusEnum): The status that was set.
        changed_at (DateTime): Timestamp of when the status change occurred.
        changed_by_id (int, optional): Foreign key linking to the user who initiated the status change.
                                     Can be null if the change was automated by the system.
        notes (str, optional): Additional notes or reasons for the status change.

        request (relationship): Relationship to the Request this history entry belongs to.
        changed_by (relationship): Relationship to the User who initiated the change.
    """
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)

    status = Column(SQLAlchemyEnum(RequestStatusEnum), nullable=False)

    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String, nullable=True)

    request = relationship("Request", back_populates="status_history")
    changed_by = relationship("User", back_populates="status_changes")

    def __repr__(self):
        """String representation of the RequestStatusHistory object."""
        return f"<RequestStatusHistory(id={self.id}, request_id={self.request_id}, status='{self.status.value if self.status else None}')>"
