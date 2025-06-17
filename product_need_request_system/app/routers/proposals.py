from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from datetime import date # For date comparisons

from app import crud, models, schemas
from app.database import get_db
from app.security import get_current_user, require_supplier, require_admin # Import new security

router = APIRouter(
    prefix="/api/v1/requests/{request_id}/proposals",
    tags=["Proposals"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Proposal, status_code=status.HTTP_201_CREATED)
def create_proposal_endpoint(
    request_id: int,
    proposal: schemas.ProposalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_supplier) # User must be a Supplier
):
    # current_user.role is already validated by require_supplier
    # No need for: if current_user.role != schemas.UserRole.SUPPLIER.value: ...

    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    if db_request.status != schemas.RequestStatus.APPROVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposals can only be submitted for 'approved' requests.")

    if db_request.expiration_date < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot submit proposal for an expired request.")

    existing_proposal = crud.get_proposal_by_request_and_supplier(db, request_id=request_id, supplier_id=current_user.id)
    if existing_proposal:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier already submitted a proposal for this request.")

    return crud.create_proposal(db=db, proposal=proposal, request_id=request_id, supplier_id=current_user.id)


@router.get("/", response_model=List[schemas.Proposal])
def list_proposals_for_request_endpoint(
    request_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # General authenticated user
):
    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    is_admin = current_user.role == schemas.UserRole.ADMIN.value
    is_request_owner = db_request.user_id == current_user.id
    is_supplier = current_user.role == schemas.UserRole.SUPPLIER.value # Check current user's role

    # Allow if admin, request owner, or a supplier (general supplier access to see proposals for an approved request)
    # More granular: check if current_supplier is one of the proposers for this request.
    # For now, any supplier can see proposals on an approved request.
    if not (is_admin or is_request_owner or is_supplier):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view proposals for this request.")

    return crud.get_proposals_by_request(db=db, request_id=request_id, skip=skip, limit=limit)

@router.get("/{proposal_id}", response_model=schemas.Proposal)
def get_single_proposal_endpoint(
    request_id: int,
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_proposal = crud.get_proposal(db, proposal_id=proposal_id)
    if not db_proposal or db_proposal.request_id != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found for this request.")

    db_request = crud.get_request(db, request_id=db_proposal.request_id) # Fetch request for owner ID
    if not db_request: # Should not happen if proposal links to valid request
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated request not found.")


    is_admin = current_user.role == schemas.UserRole.ADMIN.value
    is_proposal_supplier = db_proposal.supplier_id == current_user.id
    is_request_owner = db_request.user_id == current_user.id

    if not (is_admin or is_proposal_supplier or is_request_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this proposal.")

    return db_proposal

@router.put("/{proposal_id}", response_model=schemas.Proposal)
def update_proposal_endpoint(
    request_id: int,
    proposal_id: int,
    proposal_update: schemas.ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_supplier) # Must be a supplier
):
    db_proposal = crud.get_proposal(db, proposal_id=proposal_id)
    if not db_proposal or db_proposal.request_id != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found for this request.")

    if db_proposal.supplier_id != current_user.id: # Must be owner of the proposal
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this proposal. Must be the owner.")

    db_request = crud.get_request(db, request_id=db_proposal.request_id)
    if not db_request:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated request not found.")

    if db_request.status != schemas.RequestStatus.APPROVED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposals can only be updated if the request is 'approved'.")

    if db_request.expiration_date < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update proposal for an expired request.")

    if proposal_update.quantity is None or proposal_update.quantity < 1: # Validator in schema handles >=1, but explicit check for None
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantity must be provided and be at least 1.")

    return crud.update_proposal_quantity(db=db, db_proposal=db_proposal, quantity=proposal_update.quantity)

@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal_endpoint(
    request_id: int,
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # General user for initial check
):
    db_proposal = crud.get_proposal(db, proposal_id=proposal_id)
    if not db_proposal or db_proposal.request_id != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found for this request.")

    is_admin = current_user.role == schemas.UserRole.ADMIN.value
    is_proposal_owner_supplier = (current_user.role == schemas.UserRole.SUPPLIER.value and \
                                  db_proposal.supplier_id == current_user.id)

    if not (is_admin or is_proposal_owner_supplier):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this proposal. Must be admin or proposal owner.")

    db_request = crud.get_request(db, request_id=db_proposal.request_id)
    if not db_request:
         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated request not found.")

    # Allow deletion if request is 'approved' (for owner supplier) or if user is admin
    if db_request.status != schemas.RequestStatus.APPROVED.value and not is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Proposal can only be deleted by its owner if the request is 'approved'. Admin can delete under more conditions.")

    crud.delete_proposal(db=db, db_proposal=db_proposal)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
