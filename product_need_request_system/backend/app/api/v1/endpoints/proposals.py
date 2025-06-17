"""
API Endpoints for Proposal Management.

Provides endpoints for creating and reading proposals related to product/service requests.
Access control is applied based on user roles (Supplier, Request Owner, Admin).
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import crud, models, schemas # models for UserModel, schemas for I/O
from app.api import deps # For common dependencies
from app.models.user import User as UserModel # Explicit import for type hinting

router = APIRouter()

# --- Helper Dependency for Supplier Role Check (specific to this module) ---
def _require_supplier_role(current_user: UserModel = Depends(deps.get_current_active_user)):
    """
    Dependency that checks if the current user has the 'Supplier' role.
    Raises HTTPException 403 if not.
    """
    if not any(role.name == "Supplier" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires Supplier privileges."
        )
    return current_user

# --- Proposal Endpoints ---

@router.post("/", response_model=schemas.Proposal, status_code=status.HTTP_201_CREATED)
def create_proposal(
    *,
    db: Session = Depends(deps.get_db),
    proposal_in: schemas.ProposalCreate,
    current_supplier: UserModel = Depends(_require_supplier_role), # Ensures user is a Supplier
) -> Any:
    """
    Create a new proposal for an active and 'APPROVED' request.
    - Only users with the "Supplier" role can create proposals.
    - A supplier can only submit one proposal per request.
    - Proposals cannot be submitted for expired requests.
    """
    try:
        proposal = crud.proposal.create_with_supplier(
            db=db, obj_in=proposal_in, supplier_id=current_supplier.id
        )
    except ValueError as e: # Catches validation errors from CRUD (e.g., request not found, not approved, expired, duplicate proposal)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return proposal

@router.get("/", response_model=List[schemas.Proposal])
def read_proposals(
    db: Session = Depends(deps.get_db),
    current_user: UserModel = Depends(deps.get_current_active_user),
    request_id: Optional[int] = Query(None, description="Filter proposals by a specific request ID."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> Any:
    """
    Retrieve proposals based on user role and query parameters.
    - **Admins**: Can see all proposals. If `request_id` is provided, filters by that request.
    - **Suppliers**:
        - If `request_id` is NOT provided, sees all proposals they submitted.
        - If `request_id` IS provided, sees proposals for that request ONLY IF they submitted one for it.
    - **Request Owners**: If `request_id` is provided and they own the request, sees all proposals for that request.
    - **Others**: No access unless they are admin or owner of the specified `request_id`.
    """
    is_admin = any(role.name == "Admin" for role in current_user.roles)
    is_supplier = any(role.name == "Supplier" for role in current_user.roles)

    if is_admin:
        if request_id:
            proposals = crud.proposal.get_multi_by_request(db, request_id=request_id, skip=skip, limit=limit)
        else:
            # Admin getting all proposals. Assumes crud.proposal.get_multi loads relations.
            proposals = crud.proposal.get_multi(db, skip=skip, limit=limit)
    elif is_supplier:
        if not request_id: # Supplier getting all their own proposals
            proposals = crud.proposal.get_multi_by_supplier(db, supplier_id=current_user.id, skip=skip, limit=limit)
        else: # Supplier viewing proposals for a specific request
            # Check if this supplier made a proposal for this request_id
            if crud.proposal.get_by_request_and_supplier(db, request_id=request_id, supplier_id=current_user.id):
                proposals = crud.proposal.get_multi_by_request(db, request_id=request_id, skip=skip, limit=limit)
            else: # Supplier has not proposed to this request, show no proposals for it (or 403)
                proposals = []
    elif request_id: # Non-admin, non-supplier, but request_id is provided
        target_request = crud.request.get(db=db, id=request_id)
        if not target_request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        if target_request.owner_id == current_user.id: # User is the owner of the request
            proposals = crud.proposal.get_multi_by_request(db, request_id=request_id, skip=skip, limit=limit)
        else: # Not owner of this specific request
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view proposals for this request.")
    else: # Non-admin, non-supplier, no request_id specified - this case implies they can't list all.
        # Could return empty list or 403 depending on desired strictness.
        # For now, let's be strict for non-privileged users without specific context.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Specify a request_id or have Admin/Supplier role to list proposals broadly.")
    return proposals

@router.get("/{proposal_id}", response_model=schemas.Proposal)
def read_proposal(
    *,
    db: Session = Depends(deps.get_db),
    proposal_id: int,
    current_user: UserModel = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific proposal by its ID.
    Access Control:
    - **Admin**: Can see any proposal.
    - **Supplier**: Can see their own proposals.
    - **Request Owner**: Can see proposals submitted for their requests.
    The response includes supplier details and information about the associated request (including its owner).
    """
    proposal = crud.proposal.get_with_supplier_and_request(db=db, id=proposal_id)

    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    is_admin = any(role.name == "Admin" for role in current_user.roles)
    is_proposal_supplier = (proposal.supplier_id == current_user.id)
    # proposal.request is loaded by get_with_supplier_and_request
    is_request_owner = (proposal.request and proposal.request.owner_id == current_user.id)

    if not (is_admin or is_proposal_supplier or is_request_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view this proposal.")
    return proposal

# Placeholder for future PUT /proposals/{proposal_id} (Update Proposal)
# @router.put("/{proposal_id}", response_model=schemas.Proposal)
# def update_proposal(
#     *,
#     db: Session = Depends(deps.get_db),
#     proposal_id: int,
#     proposal_in: schemas.ProposalUpdate,
#     current_supplier: UserModel = Depends(_require_supplier_role),
# ):
#     """
#     Update a proposal (by the supplier who created it).
#     Restrictions apply (e.g., proposal status, request status).
#     """
#     proposal = crud.proposal.get(db=db, id=proposal_id)
#     if not proposal:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
#     if proposal.supplier_id != current_supplier.id:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions (not owner of proposal)")
#     # Add business logic: e.g., can only update if proposal/request is in a certain state.
#     # updated_proposal = crud.proposal.update(db=db, db_obj=proposal, obj_in=proposal_in)
#     # return updated_proposal
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Proposal update not yet implemented.")

# Placeholder for future DELETE /proposals/{proposal_id} (Withdraw Proposal)
# @router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_proposal(
#     *,
#     db: Session = Depends(deps.get_db),
#     proposal_id: int,
#     current_supplier: UserModel = Depends(_require_supplier_role),
# ):
#     """
#     Withdraw/delete a proposal (by the supplier who created it).
#     Restrictions apply (e.g., proposal status, request status).
#     """
#     # ... similar checks and logic as update ...
#     # crud.proposal.remove(db=db, id=proposal_id)
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Proposal deletion not yet implemented.")
