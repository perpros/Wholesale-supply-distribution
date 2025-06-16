from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.proposal import ProposalCreate, ProposalRead
from app.services.proposal_service import proposal_service
from app.services.request_service import request_service # For request related checks
from app.models.user import User as UserModel, UserRole
from app.models.proposal import Proposal # Ensure this is imported
from app.models.base import RequestStatus # For checking request status
from app.core.security import get_current_user
from app.core.permissions import require_supplier_role # Import new dependency
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}", tags=["Proposals"])

@router.post("/requests/{request_id}/proposals/", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def submit_new_proposal(
    request_id: int,
    proposal_in: ProposalCreate,
    db: Session = Depends(get_db),
    current_supplier: UserModel = Depends(require_supplier_role) # Ensures only Suppliers submit
):
    # Service layer handles validation of request status (must be APPROVED), expiration, and uniqueness
    created_proposal = proposal_service.create_proposal(
        db=db, proposal_in=proposal_in, request_id=request_id, supplier_id=current_supplier.id
    )
    return created_proposal

@router.get("/requests/{request_id}/proposals/", response_model=List[ProposalRead])
def read_proposals_for_a_request( # Logic for access is inside
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # General authenticated user
):
    request = request_service._get_request_or_404(db, request_id) # from request_service

    is_request_owner = request.requester_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN
    is_supplier_who_proposed = False

    if current_user.role == UserRole.SUPPLIER:
        # Check if this supplier has a proposal for this specific request
        existing_proposal = db.query(Proposal).filter( # Direct query for efficiency
            Proposal.request_id == request_id,
            Proposal.supplier_id == current_user.id
        ).first()
        if existing_proposal:
            is_supplier_who_proposed = True

    if not (is_request_owner or is_admin or is_supplier_who_proposed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view proposals for this request."
        )

    proposals = proposal_service.list_proposals_for_request(db, request_id=request_id, skip=skip, limit=limit)
    return proposals

@router.get("/proposals/my-proposals", response_model=List[ProposalRead])
def read_my_submitted_proposals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_supplier: UserModel = Depends(require_supplier_role) # Ensures Supplier
):
    proposals = proposal_service.list_proposals_by_supplier(db, supplier_id=current_supplier.id, skip=skip, limit=limit)
    return proposals

@router.get("/proposals/{proposal_id}", response_model=ProposalRead)
def read_single_proposal( # Logic for access is inside
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # General authenticated user
):
    proposal = proposal_service._get_proposal_or_404(db, proposal_id) # from proposal_service
    # Fetch associated request for ownership check
    request = request_service._get_request_or_404(db, proposal.request_id) # from request_service

    is_proposal_owner = proposal.supplier_id == current_user.id
    is_request_owner = request.requester_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN

    if not (is_proposal_owner or is_request_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this proposal."
        )
    return proposal
