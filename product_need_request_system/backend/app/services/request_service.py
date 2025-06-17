"""
Request Service Layer.

Contains business logic related to requests that may involve multiple models
or more complex operations than simple CRUD.
"""
from sqlalchemy.orm import Session, selectinload
# from sqlalchemy.sql import func # For potential direct DB sum, if not iterating loaded objects

from app import models # Gives access to models.Request, models.Proposal
from app.models.enums import ProposalStatusEnum # For checking proposal status

class RequestService:
    """
    Provides services for request-related business logic.
    """
    def is_request_need_met(self, db: Session, *, request_id: int) -> bool:
        """
        Checks if the total quantity from relevant proposals (e.g., SUBMITTED or ACCEPTED)
        meets or exceeds the quantity specified in a given request.

        Args:
            db: SQLAlchemy database session.
            request_id: The ID of the request to check.

        Returns:
            True if the need is met, False otherwise (including if request not found).
        """
        request = (
            db.query(models.Request)
            .options(selectinload(models.Request.proposals)) # Eager load proposals for this request
            .filter(models.Request.id == request_id)
            .first()
        )

        if not request:
            # Depending on expected usage, this could log a warning or raise an exception.
            # For a boolean check, returning False if request doesn't exist is reasonable.
            return False

        if not request.proposals:
            return False # No proposals, so the need cannot be met.

        total_proposed_quantity = 0
        # Iterate through the eagerly loaded proposals.
        # Filter by proposal status to sum only relevant proposals.
        # If an "ACCEPTED" status is introduced for proposals, that would be the primary filter.
        # For now, using SUBMITTED as per current ProposalStatusEnum.
        for proposal in request.proposals:
            if proposal.status == ProposalStatusEnum.SUBMITTED: # Or a future "ACCEPTED" status
                total_proposed_quantity += proposal.quantity

        # Alternative using a direct SQLAlchemy sum query:
        # This would avoid loading all proposal objects if only the sum is needed.
        # However, since we might need proposal details for other logic later,
        # loading them might be acceptable.
        #
        # total_proposed_quantity = db.query(func.sum(models.Proposal.quantity)).filter(
        #    models.Proposal.request_id == request_id,
        #    models.Proposal.status == ProposalStatusEnum.SUBMITTED # Or other relevant status
        # ).scalar() or 0 # .scalar() returns the sum or None if no rows; 'or 0' handles None.

        return total_proposed_quantity >= request.quantity

request_service = RequestService()
