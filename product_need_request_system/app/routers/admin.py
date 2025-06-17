from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.database import get_db
from app.schemas import RequestStatus # For query param type hint
from app.security import require_admin, get_current_user # Import new security

router = APIRouter(
    prefix="/api/v1/admin/requests",
    tags=["Admin - Requests"],
    dependencies=[Depends(require_admin)], # Apply admin auth to all routes in this router
    responses={
        # 401: {"description": "Unauthorized"}, # Handled by require_admin / get_current_user
        403: {"description": "Forbidden (user is not an Admin or action not allowed)"},
        404: {"description": "Not found"},
    },
)

@router.post("/{request_id}/accept", response_model=schemas.Request, summary="Accept a submitted request")
def admin_accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    # current_admin is guaranteed by router-level dependency. Use get_current_user to get the user object.
    acting_admin: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    if db_request.status != schemas.RequestStatus.SUBMITTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must be 'submitted' to be accepted.")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.ACCEPTED, changed_by_user_id=acting_admin.id)

@router.post("/{request_id}/reject", response_model=schemas.Request, summary="Reject a submitted or accepted request")
def admin_reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    acting_admin: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    allowed_statuses_for_rejection = [
        schemas.RequestStatus.SUBMITTED.value,
        schemas.RequestStatus.ACCEPTED.value,
        schemas.RequestStatus.RESUBMITTED.value
    ]
    if db_request.status not in allowed_statuses_for_rejection:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request in status '{db_request.status}' cannot be rejected by admin. Must be submitted, accepted, or resubmitted.")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.REJECTED, changed_by_user_id=acting_admin.id)

@router.post("/{request_id}/approve", response_model=schemas.Request, summary="Approve an accepted request")
def admin_approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    acting_admin: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    if db_request.status != schemas.RequestStatus.ACCEPTED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request must be 'accepted' to be approved.")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.APPROVED, changed_by_user_id=acting_admin.id)

@router.post("/{request_id}/cancel", response_model=schemas.Request, summary="Cancel a request (Admin action)")
def admin_cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
    acting_admin: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if not db_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found.")

    if db_request.status in [
        schemas.RequestStatus.CLOSED.value,
        schemas.RequestStatus.CANCELLED.value,
    ]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request in status '{db_request.status}' cannot be cancelled or is already cancelled.")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.CANCELLED, changed_by_user_id=acting_admin.id)

@router.get("/", response_model=List[schemas.Request], summary="List all requests (Admin view with filters)")
def admin_list_all_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[RequestStatus] = None,
    db: Session = Depends(get_db),
    # acting_admin: models.User = Depends(get_current_user) # Not strictly needed if only for auth check by router dep
):
    requests = crud.get_all_requests(db=db, skip=skip, limit=limit, status=status_filter)
    return requests
