from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM as PgEnum # Import PgEnum for PostgreSQL specific Enum type
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base # Important: Base should come from database.py

# Define Enums using Python's Enum and then create PostgreSQL Enum types
import enum

class UserRoleEnum(enum.Enum):
    END_USER = "EndUser"
    SUPPLIER = "Supplier"
    ADMIN = "Admin"

class RequestStatusEnum(enum.Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    RESUBMITTED = "resubmitted"
    EXPIRED = "expired"
    CLOSED = "closed"

# Create PostgreSQL specific ENUM types. These will be created in the DB by Alembic.
UserRole = PgEnum(UserRoleEnum, name="user_role_enum", create_type=False)
RequestStatus = PgEnum(RequestStatusEnum, name="request_status_enum", create_type=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False) # Essential for security
    role = Column(UserRole, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    requests = relationship("Request", back_populates="user")
    proposals = relationship("Proposal", back_populates="supplier")
    status_changes = relationship("RequestStatusHistory", back_populates="changed_by_user")
    notifications = relationship("Notification", back_populates="user")

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_type = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False) # CHECK constraint in migration
    promised_delivery_date = Column(Date, nullable=False)
    expiration_date = Column(Date, nullable=False)
    status = Column(RequestStatus, nullable=False, default=RequestStatusEnum.SUBMITTED)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="requests")
    proposals = relationship("Proposal", back_populates="request")
    status_history = relationship("RequestStatusHistory", back_populates="request", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="request", cascade="all, delete-orphan")

    # __table_args__ will be handled by Alembic for constraints like CHECK

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    quantity = Column(Integer, nullable=False) # CHECK constraint in migration
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("User", back_populates="proposals")
    request = relationship("Request", back_populates="proposals")

    __table_args__ = (
        UniqueConstraint('supplier_id', 'request_id', name='uq_supplier_request'),
    )

class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    status = Column(RequestStatus, nullable=False) # Use the same Enum for consistency
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Can be null for system actions

    request = relationship("Request", back_populates="status_history")
    changed_by_user = relationship("User", back_populates="status_changes")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False) # Link notification to a specific request
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False)

    user = relationship("User", back_populates="notifications")
    request = relationship("Request", back_populates="notifications")
