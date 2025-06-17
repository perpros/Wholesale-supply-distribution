from sqlalchemy import Column, Integer, Date, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.enums import ProductType, RequestStatus
# Ensure User model is available for relationship, adjust import if models are structured differently
# from .user import User # Assuming User model is in the same directory or accessible

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(SAEnum(ProductType), nullable=False)
    quantity = Column(Integer, nullable=False)
    promised_delivery_date = Column(Date, nullable=True) # Assuming this can be optional initially
    expiration_date = Column(Date, nullable=True) # Assuming this can be optional
    status = Column(SAEnum(RequestStatus), nullable=False, default=RequestStatus.SUBMITTED)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="requests")
    proposals = relationship("Proposal", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("RequestStatusHistory", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Request(id={self.id}, product_type='{self.product_type}', status='{self.status}')>"

# Add back_populates to User model for 'requests'
# In backend/app/models/user.py:
# from sqlalchemy.orm import relationship
# requests = relationship("Request", back_populates="owner")
