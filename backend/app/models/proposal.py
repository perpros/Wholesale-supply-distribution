from sqlalchemy import Column, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from backend.app.database import Base
from backend.app.models.enums import ProposalStatus
# from .user import User
# from .request import Request

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False) # User who is a supplier
    quantity_proposed = Column(Integer, nullable=False) # Renamed from quantity to avoid confusion
    # Add other proposal-specific fields like price, delivery_details, etc.
    status = Column(SAEnum(ProposalStatus), nullable=False, default=ProposalStatus.SUBMITTED)

    request = relationship("Request", back_populates="proposals")
    supplier = relationship("User", back_populates="proposals")

    def __repr__(self):
        return f"<Proposal(id={self.id}, request_id={self.request_id}, supplier_id={self.supplier_id}, status='{self.status}')>"

# Add back_populates to User model for 'proposals'
# In backend/app/models/user.py:
# proposals = relationship("Proposal", back_populates="supplier")
