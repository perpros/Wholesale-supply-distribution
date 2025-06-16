# Import Base from app.models.base
from app.models.base import Base

# Import all models here so that Base knows about them for Alembic migrations
# Alembic needs to be able to find the metadata object.
from app.models.user import User
from app.models.request import Request
from app.models.proposal import Proposal
from app.models.request_status_history import RequestStatusHistory

# You can also define any common database utility functions or base classes here if needed,
# but for now, it primarily serves to ensure all models are discoverable by Alembic
# through the Base.metadata object.
