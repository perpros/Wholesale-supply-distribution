from sqlalchemy import Column, Integer, Enum as SQLAlchemyEnum, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.models.base import Base, RequestStatus # Re-using RequestStatus enum

class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLAlchemyEnum(RequestStatus), nullable=False) # The status it was changed to
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    request = relationship("Request", back_populates="status_history")

    # Optional: Log which user made the change. Can be null if system changed it.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # user = relationship("User") # If you need to access user details from history

    def __repr__(self):
        return f"<RequestStatusHistory(id={self.id}, request_id={self.request_id}, status='{self.status.value}')>"
