from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app import crud, models, schemas
from backend.app.database import get_db
from backend.app.security.jwt import get_current_user
# from backend.app.schemas.user import User as UserSchema

router = APIRouter()

@router.post("/", response_model=schemas.Proposal, status_code=status.HTTP_201_CREATED)
def create_proposal(
    *,
    db: Annotated[Session, Depends(get_db)],
    proposal_in: schemas.ProposalCreate, # Contains request_id
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Proposal:
    """
    Create new proposal for a request.
    Requires `request_id` in the payload.
    Placeholder: Supplier role check.
    """
    # TODO: Implement role check: Supplier only
    # For now, any authenticated user can create a proposal.
    # current_user is now a models.User instance
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # TODO: Implement role check: Supplier only
    # Example: if current_user.role != "supplier":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only suppliers can create proposals")

    # Check if the request exists
    request_obj = crud.request.get(db=db, id=proposal_in.request_id)
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request with id {proposal_in.request_id} not found.")

    # TODO: Check if supplier is trying to propose on their own request (if applicable)
    # if request_obj.owner_id == current_user.id:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create a proposal for your own request.")

    created_proposal = crud.proposal.create_with_supplier_and_request(
        db=db, obj_in=proposal_in, supplier_id=current_user.id
    )
    return created_proposal

@router.get("/by_request/{request_id}", response_model=List[schemas.Proposal])
def read_proposals_for_request(
    *,
    db: Annotated[Session, Depends(get_db)],
    request_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> List[models.Proposal]:
    """
    Retrieve proposals for a specific request.
    TODO: Access control: request owner, proposal supplier, or admin.
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    request_obj = crud.request.get(db=db, id=request_id)
    if not request_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Placeholder: check if current_user is owner of request, the supplier who made proposals, or admin
    # This requires more complex logic if suppliers can only see their own proposals on a request unless they are the request owner.
    # For now, let's assume if you are authenticated, you can see proposals for a valid request.
    # A stricter check:
    # if not (hasattr(current_user, 'id') and hasattr(current_user, 'role') and \
    #         (request_obj.owner_id == current_user.id or current_user.role == "admin")):
    #     # Check if current user is a supplier for any of the proposals on this request
    #     is_supplier_for_request = any(p.supplier_id == current_user.id for p in request_obj.proposals)
    #     if not is_supplier_for_request:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    pass # Soft pass for now

    proposals = crud.proposal.get_multi_by_request(db, request_id=request_id, skip=skip, limit=limit)
    return proposals

@router.get("/{proposal_id}", response_model=schemas.Proposal)
def read_proposal(
    *,
    db: Annotated[Session, Depends(get_db)],
    proposal_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Proposal:
    """
    Get proposal by ID.
    TODO: Check ownership (supplier or request owner) or admin role.
    """
    proposal = crud.proposal.get(db=db, id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    # Placeholder for ownership/role check
    # request_obj = crud.request.get(db=db, id=proposal.request_id) # Fetch request to check its owner
    # if not (hasattr(current_user, 'id') and hasattr(current_user, 'role') and \
    #         (proposal.supplier_id == current_user.id or \
    #          (request_obj and request_obj.owner_id == current_user.id) or \
    #          current_user.role == "admin")):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    pass # Soft pass for now
    return proposal

@router.put("/{proposal_id}", response_model=schemas.Proposal)
def update_proposal(
    *,
    db: Annotated[Session, Depends(get_db)],
    proposal_id: int,
    proposal_in: schemas.ProposalUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Proposal:
    """
    Update a proposal.
    TODO: Check ownership (supplier) or admin role.
    """
    proposal = crud.proposal.get(db=db, id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    # Placeholder for ownership (supplier) check
    if not (hasattr(current_user, 'id') and hasattr(current_user, 'role') and \
            (proposal.supplier_id == current_user.id or current_user.role == "admin")):
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        pass # Soft pass for now

    updated_proposal = crud.proposal.update(db=db, db_obj=proposal, obj_in=proposal_in)
    return updated_proposal

@router.delete("/{proposal_id}", response_model=schemas.Proposal)
def delete_proposal(
    *,
    db: Annotated[Session, Depends(get_db)],
    proposal_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Proposal:
    """
    Delete a proposal.
    TODO: Check ownership (supplier) or admin role.
    """
    proposal = crud.proposal.get(db=db, id=proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    # Placeholder for ownership (supplier) check
    # if proposal.supplier_id != current_user.id and current_user.role != "admin":
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    deleted_proposal = crud.proposal.remove(db=db, id=proposal_id)
    if not deleted_proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found during deletion")
    return deleted_proposal
