from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # for datetime.utcnow

from backend.app.database import Base
# from .request import Request
# from .user import User

class RequestStatusHistory(Base):
    __tablename__ = "request_status_histories"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    # Storing enum string value, not SAEnum itself, for flexibility if enum changes
    # or if you want to record arbitrary status strings not in current enum (though less ideal)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable if system change

    request = relationship("Request", back_populates="status_history")
    changed_by = relationship("User", back_populates="status_changes") # Name of relationship in User

    def __repr__(self):
        return f"<RequestStatusHistory(id={self.id}, request_id={self.request_id}, status='{self.status}', timestamp='{self.timestamp}')>"

# Add back_populates to User model for 'status_changes'
# In backend/app/models/user.py:
# status_changes = relationship("RequestStatusHistory", back_populates="changed_by")
