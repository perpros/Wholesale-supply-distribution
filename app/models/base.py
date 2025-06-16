from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData, Column, DateTime, func, text
from enum import Enum as PyEnum

class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    # Optional: Common columns for all tables, like created_at and updated_at
    # created_at = Column(DateTime(timezone=True), server_default=func.now())
    # updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserRole(PyEnum):
    END_USER = "End User"
    SUPPLIER = "Supplier"
    ADMIN = "Admin"
    # SYSTEM_SCHEDULER is a conceptual role for actions, not a loginable user type.

class RequestStatus(PyEnum):
    SUBMITTED = "Submitted"
    APPROVED = "Approved" # Approved by Admin, open for proposals
    REJECTED = "Rejected" # Rejected by Admin
    EXPIRED = "Expired" # Past expiration_date
    CLOSED = "Closed" # Need met or manually closed
    CANCELLED = "Cancelled" # Cancelled by user or admin

class ProposalStatus(PyEnum):
    SUBMITTED = "Submitted"
    ACCEPTED = "Accepted" # Proposal chosen for the request
    REJECTED = "Rejected" # Proposal not chosen

class ProductType(PyEnum):
    TYPE_A = "Type A"
    TYPE_B = "Type B"
    TYPE_C = "Type C"
    # Add more product types as needed
