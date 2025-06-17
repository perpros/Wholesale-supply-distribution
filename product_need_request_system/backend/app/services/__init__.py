# This file makes 'services' a Python package.
# It will contain business logic services that orchestrate operations,
# potentially interacting with multiple CRUD modules or external services.
from .request_service import request_service

__all__ = ["request_service"]
