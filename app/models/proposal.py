from sqlalchemy import Column, Integer, Enum as SQLAlchemyEnum, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import relationship
from app.models.base import Base, ProposalStatus

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False) # Assuming integer quantity
    # unit_price = Column(Numeric(10, 2)) # Example if proposals have pricing
    # comments = Column(String) # Example for additional proposal details

    status = Column(SQLAlchemyEnum(ProposalStatus), nullable=False, default=ProposalStatus.SUBMITTED)

    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    request = relationship("Request", back_populates="proposals")

    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier = relationship("User", back_populates="proposals")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Proposal(id={self.id}, request_id={self.request_id}, supplier_id={self.supplier_id}, status='{self.status.value}')>"
