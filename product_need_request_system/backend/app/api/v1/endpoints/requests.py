"""
API Endpoints for Request Management.

Provides endpoints for creating, reading, updating, and managing the lifecycle
of product/service requests. Access control is applied based on user roles
(End User, Admin).
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from app import crud, models, schemas # models for UserModel, schemas for I/O
from app.api import deps # For common dependencies
from app.models.enums import RequestStatusEnum # For status comparisons and types

router = APIRouter()

# --- Helper Dependency for Admin Role Check (specific to this module) ---
def _require_admin_role(current_user: models.User = Depends(deps.get_current_active_user)):
    """
    Dependency that checks if the current user has the 'Admin' role.
    Raises HTTPException 403 if not.
    """
    if not any(role.name == "Admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation requires Admin privileges."
        )
    return current_user

# --- Request Endpoints ---

@router.post("/", response_model=schemas.Request, status_code=status.HTTP_201_CREATED)
def create_request(
    *,
    db: Session = Depends(deps.get_db),
    request_in: schemas.RequestCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a new product or service request.
    Any authenticated and active user can create a request.
    The request is initially set to 'SUBMITTED' status.
    """
    # Optional: Add explicit role check if only users with a specific role (e.g., "End User") can create.
    # For now, any active authenticated user can create.
    # Example: if not any(role.name == "End User" for role in current_user.roles):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only 'End Users' can create requests.")
    try:
        request = crud.request.create_with_owner(db=db, obj_in=request_in, owner_id=current_user.id)
    except ValueError as e: # Catch validation errors from Pydantic models or CRUD layer
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return request

@router.get("/", response_model=List[schemas.Request])
def read_requests(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    # status_filter: Optional[RequestStatusEnum] = Query(None, alias="status") # Example for future filtering
) -> Any:
    """
    Retrieve requests.
    - Users with "Admin" role can see all requests.
    - Other authenticated users (e.g., "End User") see only their own requests.
    Requests for admins are returned with owner information loaded.
    """
    is_admin = any(role.name == "Admin" for role in current_user.roles)

    if is_admin:
        # Admin: Get all requests, with owner details loaded (modification needed in CRUD)
        requests = crud.request.get_multi(db, skip=skip, limit=limit, load_owner=True) # Assumes get_multi is updated
    else:
        # Non-Admin: Get only their own requests
        requests = crud.request.get_multi_by_owner(db=db, owner_id=current_user.id, skip=skip, limit=limit)
    return requests

@router.get("/{request_id}", response_model=schemas.Request)
def read_request(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific request by its ID.
    - Users with "Admin" role can see any request.
    - Other authenticated users can only see their own requests.
    Includes owner and status history details.
    """
    request = crud.request.get_with_owner_and_history(db=db, id=request_id) # Fetches with owner and history

    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    is_admin = any(role.name == "Admin" for role in current_user.roles)
    if not is_admin and request.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions to view this request")
    return request

@router.put("/{request_id}", response_model=schemas.Request)
def update_request_by_owner(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    request_in: schemas.RequestUpdate, # Schema for updating request fields
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a request's fields (by the owner).
    - Only the owner of the request can update its details.
    - Updates are only allowed if the request is in 'SUBMITTED' or 'REJECTED' status.
    """
    request = crud.request.get(db=db, id=request_id) # Get the existing request
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if request.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions (not owner)")

    try:
        # crud.request.update_request_fields handles status check and date validation logic
        updated_request = crud.request.update_request_fields(
            db=db, db_obj=request, obj_in=request_in, user_id=current_user.id
        )
        if updated_request is None:
             # This case implies CRUD method returned None due to business rule (e.g. status block)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Request cannot be updated in its current status: {request.status.value}"
            )
    except ValueError as e: # Catch validation errors from Pydantic models or CRUD custom validation
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return updated_request

# --- End User Actions for Status Changes ---
@router.post("/{request_id}/cancel", response_model=schemas.Request, summary="Cancel Request (User)")
def cancel_request_by_user(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Allows an End User to cancel their own request.
    Cancellation is permitted if the request is in 'SUBMITTED' or 'APPROVED' status.
    """
    req = crud.request.get(db=db, id=request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions (not owner)")

    if req.status not in [RequestStatusEnum.SUBMITTED, RequestStatusEnum.APPROVED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request cannot be cancelled by user in its current status: {req.status.value}"
        )
    notes = "Request cancelled by user."
    updated_req = crud.request.update_status(db, db_obj=req, new_status=RequestStatusEnum.CANCELLED, user_id=current_user.id, notes=notes)
    return updated_req

@router.post("/{request_id}/resubmit", response_model=schemas.Request, summary="Resubmit Request (User)")
def resubmit_request_by_user(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
    # Optional: request_in: schemas.RequestUpdate = Body(None) # Allow updates on resubmit
) -> Any:
    """
    Allows an End User to resubmit their own request if it was 'REJECTED'.
    The request status is changed back to 'SUBMITTED'.
    Optionally, fields can be updated during resubmission if `request_in` is provided.
    """
    req = crud.request.get(db=db, id=request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if req.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions (not owner)")

    if req.status != RequestStatusEnum.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request can only be resubmitted if in REJECTED status. Current: {req.status.value}"
        )

    # Example: If updates are allowed on resubmit
    # if request_in:
    #     try:
    #         req = crud.request.update_request_fields(db=db, db_obj=req, obj_in=request_in, user_id=current_user.id)
    #         if req is None: # Should not happen if status is REJECTED as per update_request_fields logic
    #             raise HTTPException(status_code=400, detail="Update during resubmit failed due to field validation or status.")
    #     except ValueError as e:
    #         raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    #     db.refresh(req)

    notes = "Request resubmitted by user."
    updated_req = crud.request.update_status(db, db_obj=req, new_status=RequestStatusEnum.SUBMITTED, user_id=current_user.id, notes=notes)
    return updated_req

# --- Admin Actions for Status Changes ---
@router.post("/{request_id}/approve", response_model=schemas.Request, summary="Approve Request (Admin)")
def approve_request_by_admin(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    admin_user: models.User = Depends(_require_admin_role),
) -> Any:
    """
    Allows an Admin to approve a request.
    Typically transitions a 'SUBMITTED' request to 'APPROVED', making it open for proposals.
    """
    req = crud.request.get(db=db, id=request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != RequestStatusEnum.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request can only be approved if SUBMITTED. Current status: {req.status.value}")

    notes = f"Request approved by admin ({admin_user.email})."
    updated_req = crud.request.update_status(db, db_obj=req, new_status=RequestStatusEnum.APPROVED, user_id=admin_user.id, notes=notes)
    return updated_req

@router.post("/{request_id}/reject", response_model=schemas.Request, summary="Reject Request (Admin)")
def reject_request_by_admin(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    admin_user: models.User = Depends(_require_admin_role),
    rejection_notes: Optional[str] = Body(None, embed=True, alias="notes"), # Admin can provide rejection notes
) -> Any:
    """
    Allows an Admin to reject a request.
    Typically transitions a 'SUBMITTED' request to 'REJECTED'.
    """
    req = crud.request.get(db=db, id=request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != RequestStatusEnum.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request can only be rejected if SUBMITTED. Current status: {req.status.value}")

    notes = f"Request rejected by admin ({admin_user.email}). Reason: {rejection_notes or 'Not specified'}."
    updated_req = crud.request.update_status(db, db_obj=req, new_status=RequestStatusEnum.REJECTED, user_id=admin_user.id, notes=notes)
    return updated_req

@router.post("/{request_id}/admin-cancel", response_model=schemas.Request, summary="Cancel Request (Admin)")
def cancel_request_by_admin(
    *,
    db: Session = Depends(deps.get_db),
    request_id: int,
    admin_user: models.User = Depends(_require_admin_role),
    cancellation_notes: Optional[str] = Body(None, embed=True, alias="notes"),
) -> Any:
    """
    Allows an Admin to cancel a request.
    Admins have more leniency on which statuses can be cancelled compared to users.
    """
    req = crud.request.get(db=db, id=request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Prevent cancelling already closed or cancelled requests
    if req.status in [RequestStatusEnum.CLOSED_FULFILLED, RequestStatusEnum.CLOSED_UNFULFILLED, RequestStatusEnum.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request cannot be cancelled by admin in its current status: {req.status.value}")

    notes = f"Request cancelled by admin ({admin_user.email}). Reason: {cancellation_notes or 'Not specified'}."
    updated_req = crud.request.update_status(db, db_obj=req, new_status=RequestStatusEnum.CANCELLED, user_id=admin_user.id, notes=notes)
    return updated_req
