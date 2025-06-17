"""Proposal model definition."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base # Adjusted import path
from .enums import ProposalStatusEnum


class Proposal(Base):
    """
    Represents a proposal made by a supplier in response to a request.

    Attributes:
        id (int): Primary key for the proposal.
        request_id (int): Foreign key linking to the request this proposal is for.
        supplier_id (int): Foreign key linking to the user (supplier) who made this proposal.
        quantity (int): The quantity of product/service offered in this proposal.
        status (ProposalStatusEnum): Current status of the proposal.
        created_at (DateTime): Timestamp of when the proposal was created.
        updated_at (DateTime): Timestamp of the last update to the proposal.

        request (relationship): Relationship to the Request this proposal belongs to.
        supplier (relationship): Relationship to the User (supplier) who made this proposal.
    """
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False) # User with "Supplier" role
    quantity = Column(Integer, nullable=False)

    status = Column(SQLAlchemyEnum(ProposalStatusEnum), nullable=False, default=ProposalStatusEnum.SUBMITTED)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    request = relationship("Request", back_populates="proposals")
    supplier = relationship("User", back_populates="proposals")

    __table_args__ = (UniqueConstraint('request_id', 'supplier_id', name='uq_proposal_request_supplier'),)

    def __repr__(self):
        """String representation of the Proposal object."""
        return f"<Proposal(id={self.id}, request_id={self.request_id}, supplier_id={self.supplier_id})>"
