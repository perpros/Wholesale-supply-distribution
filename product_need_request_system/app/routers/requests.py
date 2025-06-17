from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.database import get_db
from app.schemas import RequestStatus # For query param type hint
from app.security import get_current_user, require_admin, require_end_user # Import new security

router = APIRouter(
    prefix="/api/v1/requests",
    tags=["Requests"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Request, status_code=status.HTTP_201_CREATED)
def create_request_endpoint(
    request: schemas.RequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # General authenticated user
):
    # Authorization: Typically EndUsers or Admins can create requests.
    # Suppliers usually don't create product requests for themselves in this system.
    if current_user.role not in [schemas.UserRole.END_USER.value, schemas.UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User with role '{current_user.role}' cannot create requests."
        )
    return crud.create_request(db=db, request=request, user_id=current_user.id)

@router.get("/", response_model=List[schemas.Request])
def read_all_or_own_requests_endpoint(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[RequestStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role == schemas.UserRole.ADMIN.value:
        return crud.get_all_requests(db=db, skip=skip, limit=limit, status=status_filter)
    # EndUsers and Suppliers see only their own requests by default through this endpoint
    # More specific supplier views (e.g., for approved requests they can bid on) might be separate
    return crud.get_requests_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/mine", response_model=List[schemas.Request], summary="Get requests created by the current user")
def read_my_requests_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Any authenticated user can see their own
):
    return crud.get_requests_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{request_id}", response_model=schemas.Request)
def read_single_request_endpoint(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if db_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if current_user.role != schemas.UserRole.ADMIN.value and db_request.user_id != current_user.id:
        # Future: Suppliers might be able to see requests they have proposals for, or if status is 'approved'
        # For now, only owner or admin.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")
    return db_request

@router.put("/{request_id}", response_model=schemas.Request, summary="Update request details")
def update_request_details_endpoint(
    request_id: int,
    request_update: schemas.RequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if db_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    is_admin = current_user.role == schemas.UserRole.ADMIN.value
    is_owner = db_request.user_id == current_user.id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this request")

    allowed_statuses_for_edit = [schemas.RequestStatus.SUBMITTED.value, schemas.RequestStatus.REJECTED.value]
    if not is_admin and db_request.status not in allowed_statuses_for_edit:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Request can only be edited by owner if in 'submitted' or 'rejected' state. Current status: {db_request.status}")

    return crud.update_request_details(db=db, db_request=db_request, request_update=request_update)

@router.post("/{request_id}/cancel", response_model=schemas.Request, summary="Cancel a request")
def cancel_request_endpoint(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_request = crud.get_request(db, request_id=request_id)
    if db_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    can_cancel = False
    if current_user.role == schemas.UserRole.ADMIN.value:
        can_cancel = True
    elif db_request.user_id == current_user.id:
        if db_request.status in [
            schemas.RequestStatus.SUBMITTED.value,
            schemas.RequestStatus.REJECTED.value,
            schemas.RequestStatus.APPROVED.value
        ]:
            can_cancel = True

    if not can_cancel:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized or request not in a cancellable state for your role.")

    if db_request.status in [
        schemas.RequestStatus.CLOSED.value,
        schemas.RequestStatus.EXPIRED.value,
        schemas.RequestStatus.CANCELLED.value
    ]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request in status '{db_request.status}' cannot be cancelled again.")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.CANCELLED, changed_by_user_id=current_user.id)

@router.post("/{request_id}/resubmit", response_model=schemas.Request, summary="Resubmit a request")
def resubmit_request_endpoint(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_end_user) # Only EndUsers can resubmit their own
):
    db_request = crud.get_request(db, request_id=request_id)
    if db_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if db_request.user_id != current_user.id: # This check is implicitly handled by require_end_user if it checks ownership
                                            # but explicit check is safer if require_end_user only checks role.
                                            # For now, assuming require_end_user only checks role.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to resubmit this request. Must be the owner.")

    allowed_statuses_for_resubmit = [
        schemas.RequestStatus.REJECTED.value,
        schemas.RequestStatus.CANCELLED.value
    ]
    # Ensure that if cancelled, it was cancelled by the user or is appropriate for resubmission
    # This might need more complex logic if e.g. admin-cancelled requests cannot be resubmitted by user
    if db_request.status not in allowed_statuses_for_resubmit:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Request can only be resubmitted if 'rejected' or 'cancelled'. Current status: {db_request.status}")

    return crud.update_request_status(db=db, db_request=db_request, new_status=schemas.RequestStatus.RESUBMITTED, changed_by_user_id=current_user.id)
