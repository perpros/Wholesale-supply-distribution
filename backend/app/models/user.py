from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship # Import relationship
from backend.app.database import Base # Ensure this import path is correct
# Import related models if needed for type hinting or specific relationship setups,
# though string-based relationship definitions often suffice.
# from .request import Request # Example
# from .proposal import Proposal # Example
# from .request_status_history import RequestStatusHistory # Example

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") # e.g., "user", "admin", "manager"

    # Relationships
    requests = relationship("Request", back_populates="owner", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="supplier", cascade="all, delete-orphan")
    status_changes = relationship("RequestStatusHistory", back_populates="changed_by") # No cascade delete here, as history might be kept even if user is deleted, or handled by DB constraint

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
