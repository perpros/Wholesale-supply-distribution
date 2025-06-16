from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import relationship
from app.models.base import Base, RequestStatus, ProductType

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(SQLAlchemyEnum(ProductType), nullable=False)
    quantity = Column(Integer, nullable=False) # Assuming integer quantity
    # Consider using Numeric for monetary values if product_specification involves price
    # product_specification = Column(JSON) # Or define a more structured way

    promised_delivery_date = Column(DateTime(timezone=True), nullable=False)
    expiration_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLAlchemyEnum(RequestStatus), nullable=False, default=RequestStatus.SUBMITTED)

    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requester = relationship("User", back_populates="requests")

    proposals = relationship("Proposal", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("RequestStatusHistory", back_populates="request", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Request(id={self.id}, product_type='{self.product_type.value}', status='{self.status.value}')>"
