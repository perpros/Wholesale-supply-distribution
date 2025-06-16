from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.request import Request
from app.models.request_status_history import RequestStatusHistory
from app.models.user import User as UserModel, UserRole
from app.schemas.request import RequestCreate, RequestUpdate
from app.models.base import RequestStatus, ProposalStatus # Added ProposalStatus for the new method

class RequestService:
    def _get_request_or_404(self, db: Session, request_id: int) -> Request:
        request = db.query(Request).filter(Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        return request

    def _log_status_change(self, db: Session, request_id: int, new_status: RequestStatus, user_id: Optional[int]):
        history_entry = RequestStatusHistory(
            request_id=request_id,
            status=new_status,
            user_id=user_id
        )
        db.add(history_entry)

    def create_request(self, db: Session, request_in: RequestCreate, user_id: int) -> Request:
        db_request = Request(
            **request_in.model_dump(),
            requester_id=user_id,
            status=RequestStatus.SUBMITTED
        )
        db.add(db_request)
        db.flush()
        self._log_status_change(db, request_id=db_request.id, new_status=RequestStatus.SUBMITTED, user_id=user_id)
        db.commit()
        db.refresh(db_request)
        return db_request

    def get_request_by_id(self, db: Session, request_id: int) -> Optional[Request]:
        # Uses the helper now for consistency, or keep as is if 404 not desired here directly
        return db.query(Request).filter(Request.id == request_id).first()


    def list_requests_for_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Request]:
        return db.query(Request).filter(Request.requester_id == user_id).offset(skip).limit(limit).all()

    def list_all_requests(self, db: Session, skip: int = 0, limit: int = 100) -> List[Request]:
        return db.query(Request).offset(skip).limit(limit).all()

    def update_request(self, db: Session, request_id: int, request_in: RequestUpdate, current_user: UserModel) -> Request:
        db_request = self._get_request_or_404(db, request_id)

        if db_request.requester_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this request")

        if db_request.status not in [RequestStatus.SUBMITTED, RequestStatus.REJECTED]: # Allow editing if rejected
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request cannot be edited in '{db_request.status.value}' status"
            )

        update_data = request_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_request, field, value)

        # If status is part of RequestUpdate and is changed, log it.
        # However, plan implies status changes are via specific endpoints.
        # For now, direct status change in update_request is not handled/logged.
        # If an update implies a re-submission from REJECTED, status should be handled.
        if db_request.status == RequestStatus.REJECTED and update_data:
             # Assuming any update to a REJECTED request makes it SUBMITTED again.
             # This might need more specific handling or a dedicated resubmit endpoint logic.
             # For now, let's say an edit on a rejected request implicitly resubmits it.
            db_request.status = RequestStatus.SUBMITTED
            self._log_status_change(db, request_id=db_request.id, new_status=RequestStatus.SUBMITTED, user_id=current_user.id)


        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    def _change_status_with_log(self, db: Session, db_request: Request, new_status: RequestStatus, user_id: int) -> Request:
        db_request.status = new_status
        self._log_status_change(db, request_id=db_request.id, new_status=new_status, user_id=user_id)
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request

    def cancel_request(self, db: Session, request_id: int, current_user: UserModel) -> Request:
        db_request = self._get_request_or_404(db, request_id)

        is_owner = db_request.requester_id == current_user.id
        is_admin = current_user.role == UserRole.ADMIN

        if not (is_owner or is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this request")

        # Define which statuses can be cancelled. Generally, non-closed/expired ones.
        if db_request.status in [RequestStatus.CLOSED, RequestStatus.EXPIRED, RequestStatus.CANCELLED]:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request in status '{db_request.status.value}' cannot be cancelled."
            )

        return self._change_status_with_log(db, db_request, RequestStatus.CANCELLED, current_user.id)

    def resubmit_request(self, db: Session, request_id: int, current_user: UserModel) -> Request:
        # This method might be redundant if update_request handles resubmission from REJECTED state.
        # Or it can be a dedicated explicit action.
        db_request = self._get_request_or_404(db, request_id)

        if db_request.requester_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to resubmit this request")

        if db_request.status != RequestStatus.REJECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request can only be resubmitted if in '{RequestStatus.REJECTED.value}' status"
            )

        # Potentially revert some fields or require new data for resubmission if needed.
        # For now, just changing status.
        return self._change_status_with_log(db, db_request, RequestStatus.SUBMITTED, current_user.id)

    def change_request_status_by_admin(
        self, db: Session, request_id: int, new_status: RequestStatus, admin_user: UserModel
    ) -> Request:
        if admin_user.role != UserRole.ADMIN: # This check is somewhat redundant if using an admin-only dependency
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

        db_request = self._get_request_or_404(db, request_id)

        # Add any specific logic/checks before admin changes status
        valid_admin_statuses = [
            RequestStatus.APPROVED, RequestStatus.REJECTED,
            RequestStatus.CLOSED, RequestStatus.CANCELLED
            # RequestStatus.EXPIRED is usually system-driven.
        ]
        if new_status not in valid_admin_statuses:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admin cannot set status to '{new_status.value}' through this generic endpoint."
            )

        # Example: Admin cannot approve an already expired/cancelled request.
        if db_request.status in [RequestStatus.EXPIRED, RequestStatus.CANCELLED, RequestStatus.CLOSED] and new_status == RequestStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve a request that is already '{db_request.status.value}'."
            )

        # Prevent changing status if it's already the new_status
        if db_request.status == new_status:
            return db_request # Or raise error, but idempotent is fine.

        return self._change_status_with_log(db, db_request, new_status, admin_user.id)

    def is_request_need_met(self, db: Session, request_id: int) -> bool:
        db_request = self._get_request_or_404(db, request_id)

        # Sum quantities from proposals.
        # Consider which proposal statuses should count.
        # For now, let's assume any active proposal (e.g., SUBMITTED or ACCEPTED) counts.
        # If only 'ACCEPTED' proposals count, this logic needs Proposal status management first.
        # The spec says "sum(proposals.quantity) >= request.product_specification.quantity"
        # Assuming request.quantity is what's meant by request.product_specification.quantity here.

        total_proposed_quantity = 0
        for proposal in db_request.proposals:
            # Add condition here if only certain proposal statuses count, e.g.:
            if proposal.status in [ProposalStatus.SUBMITTED, ProposalStatus.ACCEPTED]:
                 total_proposed_quantity += proposal.quantity

        return total_proposed_quantity >= db_request.quantity

request_service = RequestService()
