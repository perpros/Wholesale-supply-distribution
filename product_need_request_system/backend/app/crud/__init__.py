"""
CRUD Utilities Package.

This package contains reusable base classes and specific CRUD (Create, Read, Update, Delete)
utility functions/classes for interacting with database models.

Exports specific CRUD objects for direct use, e.g., `from app.crud import user, role, request, proposal`.
"""
from .crud_user import user
from .crud_role import role
from .crud_request import request
from .crud_request_status_history import request_status_history
from .crud_proposal import proposal # Added import for proposal CRUD

# Add other CRUD objects here as they are created in the future
# e.g., from .crud_item import item

__all__ = [
    "user",
    "role",
    "request",
    "request_status_history",
    "proposal",               # Added "proposal" to __all__
    # "item", # Example for future additions
]
