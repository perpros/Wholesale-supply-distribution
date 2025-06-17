"""Request model definition."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base # Adjusted import path assuming base.py is in the same directory
from .enums import ProductTypeEnum, RequestStatusEnum

class Request(Base):
    """
    Represents a product or service request made by a user.

    Attributes:
        id (int): Primary key for the request.
        product_type (ProductTypeEnum): Type of product or service being requested.
        quantity (int): The amount or number of units requested.
        promised_delivery_date (DateTime): Desired delivery date for the product/service.
        expiration_date (DateTime): Date when this request is no longer valid or active.
        status (RequestStatusEnum): Current status of the request.
        owner_id (int): Foreign key linking to the user who owns/created this request.
        created_at (DateTime): Timestamp of when the request was created.
        updated_at (DateTime): Timestamp of the last update to the request.

        owner (relationship): Relationship to the User who owns the request.
        proposals (relationship): Relationship to Proposals made for this request.
        status_history (relationship): Relationship to the history of status changes for this request.
    """
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)

    product_type = Column(SQLAlchemyEnum(ProductTypeEnum), nullable=False)

    quantity = Column(Integer, nullable=False)
    promised_delivery_date = Column(DateTime, nullable=False)
    expiration_date = Column(DateTime, nullable=False)

    status = Column(SQLAlchemyEnum(RequestStatusEnum), nullable=False, index=True, default=RequestStatusEnum.SUBMITTED)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Corrected table name to "users"

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="requests")
    proposals = relationship("Proposal", back_populates="request", cascade="all, delete-orphan")
    status_history = relationship("RequestStatusHistory", back_populates="request", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the Request object."""
        return f"<Request(id={self.id}, product_type='{self.product_type.value if self.product_type else None}')>"
