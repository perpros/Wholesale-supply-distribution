from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.request import RequestCreate, RequestRead, RequestUpdate
from app.services.request_service import request_service
from app.models.user import User as UserModel, UserRole
from app.core.security import get_current_user
from app.core.permissions import require_admin_role, require_end_user_role # Import new dependencies
from app.core.config import settings
from app.models.base import RequestStatus # For status checks in admin routes

router = APIRouter(prefix=f"{settings.API_V1_STR}/requests", tags=["Requests"])

@router.post("/", response_model=RequestRead, status_code=status.HTTP_201_CREATED)
def create_new_request(
    request_in: RequestCreate,
    db: Session = Depends(get_db),
    current_end_user: UserModel = Depends(require_end_user_role) # Ensures only End Users create
):
    created_request = request_service.create_request(db=db, request_in=request_in, user_id=current_end_user.id)
    return created_request

@router.get("/", response_model=List[RequestRead])
def read_all_my_or_all_requests( # Name indicates logic is inside
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # General authenticated user
):
    if current_user.role == UserRole.ADMIN:
        requests = request_service.list_all_requests(db, skip=skip, limit=limit)
    elif current_user.role == UserRole.END_USER:
        requests = request_service.list_requests_for_user(db, user_id=current_user.id, skip=skip, limit=limit)
    else: # Suppliers initially don't see a generic list of requests
        requests = []
    return requests

@router.get("/{request_id}", response_model=RequestRead)
def read_single_request( # Logic for access is inside
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    request = request_service.get_request_by_id(db, request_id=request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if request.requester_id != current_user.id and current_user.role != UserRole.ADMIN:
        # Future: Suppliers might see APPROVED requests they can bid on.
        # This would require checking request.status == RequestStatus.APPROVED
        if not (current_user.role == UserRole.SUPPLIER and request.status == RequestStatus.APPROVED):
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")
    return request

@router.put("/{request_id}", response_model=RequestRead)
def update_existing_request( # Service layer handles ownership and status checks
    request_id: int,
    request_in: RequestUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # End-user or Admin (service logic differentiates)
):
    # Service's update_request checks:
    # 1. User is owner (current_user.id == db_request.requester_id)
    # 2. Status is SUBMITTED or REJECTED
    # This means an Admin cannot edit other users' requests directly via this endpoint by default.
    # If Admin should edit any request, service logic needs adjustment or a separate Admin endpoint.
    # For now, this matches "End User: Edit Request (Submitted or Rejected)"
    if current_user.role != UserRole.END_USER: # Explicit check at router level
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the End User who owns the request can edit it.")

    updated_request = request_service.update_request(
        db=db, request_id=request_id, request_in=request_in, current_user=current_user
    )
    return updated_request

@router.post("/{request_id}/cancel", response_model=RequestRead)
def cancel_a_request( # Service layer handles ownership or Admin role
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user) # End-user or Admin
):
    # request_service.cancel_request checks if current_user is owner OR admin.
    cancelled_request = request_service.cancel_request(db=db, request_id=request_id, current_user=current_user)
    return cancelled_request

@router.post("/{request_id}/resubmit", response_model=RequestRead)
def resubmit_rejected_request( # Service layer handles ownership and status checks
    request_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_end_user_role) # Explicitly for End Users
):
    # request_service.resubmit_request checks ownership and status REJECTED
    resubmitted_request = request_service.resubmit_request(db=db, request_id=request_id, current_user=current_user)
    return resubmitted_request

# Admin specific status changes
@router.post("/{request_id}/approve", response_model=RequestRead)
def admin_approve_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin_role) # Ensures admin
):
    db_request = request_service._get_request_or_404(db, request_id) # from request_service
    if db_request.status not in [RequestStatus.SUBMITTED]: # Example: only submitted can be approved
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request cannot be approved from status '{db_request.status.value}'"
        )
    approved_request = request_service.change_request_status_by_admin(
        db=db, request_id=request_id, new_status=RequestStatus.APPROVED, admin_user=admin_user
    )
    return approved_request

@router.post("/{request_id}/reject", response_model=RequestRead)
def admin_reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin_role) # Ensures admin
):
    db_request = request_service._get_request_or_404(db, request_id)
    if db_request.status not in [RequestStatus.SUBMITTED, RequestStatus.APPROVED]: # Can reject submitted or previously approved
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request cannot be rejected from status '{db_request.status.value}'"
        )
    rejected_request = request_service.change_request_status_by_admin(
        db=db, request_id=request_id, new_status=RequestStatus.REJECTED, admin_user=admin_user
    )
    return rejected_request
