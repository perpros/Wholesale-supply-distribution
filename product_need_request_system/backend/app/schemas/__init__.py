"""
Pydantic Schemas Package.

This package aggregates all Pydantic schemas for the application,
making them easily importable via `from app.schemas import ...`.
"""
from .token import Token, TokenData
from .user import User, UserBase, UserCreate, UserUpdate, UserInDB, UserInDBBase
from .role import Role, RoleBase, RoleCreate
from .request import Request, RequestCreate, RequestUpdate
from .request_status_history import RequestStatusHistory, RequestStatusHistoryCreate
from .proposal import Proposal, ProposalCreate, ProposalUpdate


__all__ = [
    "Token", "TokenData",
    "User", "UserBase", "UserCreate", "UserUpdate", "UserInDB", "UserInDBBase",
    "Role", "RoleBase", "RoleCreate",
    "Request", "RequestCreate", "RequestUpdate",
    "RequestStatusHistory", "RequestStatusHistoryCreate",
    "Proposal", "ProposalCreate", "ProposalUpdate",
]
