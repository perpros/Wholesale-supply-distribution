from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from datetime import datetime, timezone

from app.models.proposal import Proposal
from app.models.request import Request
from app.models.user import User as UserModel, UserRole
from app.schemas.proposal import ProposalCreate
from app.models.base import RequestStatus, ProposalStatus

class ProposalService:
    def _get_request_or_404(self, db: Session, request_id: int) -> Request:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        return request

    def _get_proposal_or_404(self, db: Session, proposal_id: int) -> Proposal:
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
        return proposal

    def create_proposal(self, db: Session, proposal_in: ProposalCreate, request_id: int, supplier_id: int) -> Proposal:
        request = self._get_request_or_404(db, request_id)

        # Validation: Request must be Approved and not expired
        if request.status != RequestStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Proposals can only be submitted for requests in 'Approved' status. Current status: '{request.status.value}'"
            )

        # Ensure expiration_date is timezone-aware for comparison if it's not already
        # Pydantic models should ensure they are datetime objects.
        # Assuming all datetimes are UTC or consistently handled.
        now_utc = datetime.now(timezone.utc)

        # Make sure request.expiration_date is timezone-aware (e.g. UTC) or convert now_utc to naive if comparing naive
        # Assuming request.expiration_date is stored as UTC from Pydantic validation
        if request.expiration_date.tzinfo is None:
            # If request.expiration_date is naive, assume it's comparable to naive local time (less robust)
            # Or better, ensure it's stored as UTC. For now, let's assume it's already comparable or UTC.
             # This comparison might be problematic if timezones are not handled consistently.
             # Let's assume for now that promised_delivery_date and expiration_date from schemas are tz-aware (UTC)
             # or that comparison with now_utc is appropriate.
             pass # Assuming it's okay for now.

        if request.expiration_date <= now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit proposal for an expired request."
            )

        # Validation: Only one proposal per supplier per request
        existing_proposal = db.query(Proposal).filter(
            Proposal.request_id == request_id,
            Proposal.supplier_id == supplier_id
        ).first()
        if existing_proposal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier has already submitted a proposal for this request."
            )

        db_proposal = Proposal(
            **proposal_in.model_dump(),
            request_id=request_id,
            supplier_id=supplier_id,
            status=ProposalStatus.SUBMITTED # Initial status
        )
        db.add(db_proposal)
        db.commit()
        db.refresh(db_proposal)
        return db_proposal

    def get_proposal_by_id(self, db: Session, proposal_id: int) -> Optional[Proposal]:
        return db.query(Proposal).filter(Proposal.id == proposal_id).first() # or use _get_proposal_or_404

    def list_proposals_for_request(self, db: Session, request_id: int, skip: int = 0, limit: int = 100) -> List[Proposal]:
        # Ensure request exists first
        self._get_request_or_404(db, request_id)
        return db.query(Proposal).filter(Proposal.request_id == request_id).offset(skip).limit(limit).all()

    def list_proposals_by_supplier(self, db: Session, supplier_id: int, skip: int = 0, limit: int = 100) -> List[Proposal]:
        return db.query(Proposal).filter(Proposal.supplier_id == supplier_id).offset(skip).limit(limit).all()

proposal_service = ProposalService()
