"""
SQLAlchemy models package.

This package contains the ORM models for the application.
It exports the Base class for model declaration, and all defined models and enums.
"""
from .base import Base
from .user import User
from .role import Role, user_role_association
from .request import Request
from .proposal import Proposal
from .request_status_history import RequestStatusHistory
from .enums import ProductTypeEnum, RequestStatusEnum, ProposalStatusEnum

__all__ = [
    "Base", "User", "Role", "user_role_association",
    "Request", "Proposal", "RequestStatusHistory",
    "ProductTypeEnum", "RequestStatusEnum", "ProposalStatusEnum"
]
