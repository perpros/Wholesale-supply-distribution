"""
CRUD operations for Request model.

Includes methods for creating requests with owners, logging status changes,
and handling business logic related to request updates and status transitions.
"""
from typing import Optional, List, Union, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import date # For type hinting if needed, though schemas handle it

from app.crud.base import CRUDBase
from app.models.request import Request as RequestModel
from app.models.user import User as UserModel # For type hints if needed
from app.models.enums import RequestStatusEnum
from app.schemas.request import RequestCreate, RequestUpdate
from app.crud.crud_request_status_history import request_status_history as crud_history
from app.schemas.request_status_history import RequestStatusHistoryCreate

class CRUDRequest(CRUDBase[RequestModel, RequestCreate, RequestUpdate]):
    """
    Request-specific CRUD operations.
    """
    def _log_status_change(
        self,
        db: Session,
        request_id: int,
        new_status: RequestStatusEnum,
        user_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> None:
        """
        Helper method to log a status change for a request.
        This creates a new entry in the RequestStatusHistory table.
        """
        history_entry_in = RequestStatusHistoryCreate(
            request_id=request_id,
            status=new_status,
            changed_by_id=user_id, # Can be None for system changes
            notes=notes
        )
        crud_history.create(db, obj_in=history_entry_in)
        # Note: The commit for this history entry should be handled by the calling method's transaction.

    def create_with_owner(self, db: Session, *, obj_in: RequestCreate, owner_id: int) -> RequestModel:
        """
        Create a new request associated with an owner.
        Sets initial status to SUBMITTED and logs this initial status.
        """
        # Pydantic v2 model_dump() is equivalent to .dict() in v1
        db_obj = RequestModel(
            **obj_in.model_dump(),
            owner_id=owner_id,
            status=RequestStatusEnum.SUBMITTED # Initial status
        )
        db.add(db_obj)
        db.commit() # Commit to get db_obj.id for logging
        db.refresh(db_obj)

        self._log_status_change(
            db,
            request_id=db_obj.id,
            new_status=db_obj.status,
            user_id=owner_id,
            notes="Request created."
        )
        db.commit() # Commit the status history entry

        # Refresh again to potentially load related history if the model relationship is configured
        # and if the response schema expects it.
        db.refresh(db_obj)
        return db_obj

    def get_multi( # Overriding base get_multi to add custom loading options
        self, db: Session, *, skip: int = 0, limit: int = 100, load_owner: bool = False
    ) -> List[RequestModel]:
        query = db.query(self.model)
        if load_owner:
            query = query.options(selectinload(RequestModel.owner)) # Use selectinload for relationships
        return query.order_by(RequestModel.created_at.desc()).offset(skip).limit(limit).all()

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[RequestModel]:
        """
        Get multiple requests for a specific owner, with owner details eager loaded.
        """
        return (
            db.query(self.model)
            .filter(RequestModel.owner_id == owner_id)
            .options(selectinload(RequestModel.owner)) # Use selectinload for relationships
            .order_by(RequestModel.created_at.desc()) # Example ordering
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_owner_and_history(self, db: Session, id: int) -> Optional[RequestModel]:
        """
        Get a single request by ID, with its owner and status history eagerly loaded.
        """
        return (
            db.query(self.model)
            .options(
                selectinload(RequestModel.owner),
                selectinload(RequestModel.status_history) # Eager load status history
            )
            .filter(self.model.id == id)
            .first()
        )

    def update_request_fields( # Renamed to distinguish from status updates
        self, db: Session, *, db_obj: RequestModel, obj_in: Union[RequestUpdate, Dict[str, Any]], user_id: int # user_id for audit if needed
    ) -> Optional[RequestModel]:
        """
        Update fields of a request. Restricted based on current status.
        Validates date logic if dates are part of the update.
        """
        # Business rule: Only allow updates if status is SUBMITTED or REJECTED (allowing correction)
        if db_obj.status not in [RequestStatusEnum.SUBMITTED, RequestStatusEnum.REJECTED]:
            # Or raise HTTPException directly in endpoint / service layer
            # For now, returning None indicates update was not allowed or failed.
            # Consider a custom exception for more clarity.
            # raise ValueError(f"Request cannot be updated in its current status: {db_obj.status.value}")
            return None

        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)

        # Validate date logic if both are being updated or one exists and other is updated
        promised_date = update_data.get('promised_delivery_date', db_obj.promised_delivery_date)
        expiration_date = update_data.get('expiration_date', db_obj.expiration_date)

        if promised_date and expiration_date: # Ensure dates are valid if present
            if isinstance(promised_date, str): promised_date = date.fromisoformat(promised_date)
            if isinstance(expiration_date, str): expiration_date = date.fromisoformat(expiration_date)

            if expiration_date <= promised_date:
                raise ValueError("Expiration date must be after promised delivery date during update.")
            if promised_date <= date.today() and 'promised_delivery_date' in update_data : # only check if it's a new date
                 raise ValueError("Promised delivery date must be in the future.")
            if expiration_date <= date.today() and 'expiration_date' in update_data : # only check if it's a new date
                 raise ValueError("Expiration date must be in the future.")


        # Field updates do not inherently log a new status unless status itself changes.
        # If auditing field changes is needed, that's a separate mechanism (e.g. audit log table).
        updated_request = super().update(db, db_obj=db_obj, obj_in=update_data)
        # db.commit() is called by super().update()
        # db.refresh(updated_request) is called by super().update()
        return updated_request

    def update_status(
        self, db: Session, *, db_obj: RequestModel, new_status: RequestStatusEnum, user_id: Optional[int], notes: Optional[str] = None
    ) -> RequestModel:
        """
        Update the status of a request and log this change in the history.
        Includes basic business logic for status transitions (can be expanded).
        """
        if db_obj.status == new_status:
            return db_obj # No change needed

        # --- Example Business Logic for Status Transitions ---
        # if new_status == RequestStatusEnum.APPROVED:
        #     if db_obj.status != RequestStatusEnum.SUBMITTED:
        #         raise ValueError(f"Request can only be Approved if currently in '{RequestStatusEnum.SUBMITTED.value}' status.")
        # elif new_status == RequestStatusEnum.REJECTED:
        #     if db_obj.status != RequestStatusEnum.SUBMITTED:
        #          raise ValueError(f"Request can only be Rejected if currently in '{RequestStatusEnum.SUBMITTED.value}' status.")
        # Add more transition rules as needed for your workflow.

        db_obj.status = new_status
        db.add(db_obj) # Mark the object as dirty

        self._log_status_change(db, request_id=db_obj.id, new_status=new_status, user_id=user_id, notes=notes)

        db.commit() # Commit both request status update and history log
        db.refresh(db_obj) # Refresh to get updated state and potentially new history relationship
        return db_obj

    # Placeholder for other specific actions:
    # def cancel_request(self, db: Session, *, request_id: int, user_id: int) -> RequestModel:
    #     db_obj = self.get(db, id=request_id)
    #     if not db_obj:
    #         raise ValueError("Request not found") # Or HTTPException in endpoint
    #     # Add logic: who can cancel? (owner, admin), in what statuses?
    #     return self.update_status(db, db_obj=db_obj, new_status=RequestStatusEnum.CANCELLED, user_id=user_id, notes="Request cancelled by user.")

request = CRUDRequest(RequestModel)
