"""
CRUD operations for Proposal model.

Includes methods for creating proposals with supplier validation,
and retrieving proposals based on various criteria (supplier, request).
"""
from typing import Optional, List, Union, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.proposal import Proposal as ProposalModel
from app.models.request import Request as RequestModel # To check request status/expiration
from app.models.user import User as UserModel # For type hints if needed
from app.models.enums import RequestStatusEnum, ProposalStatusEnum
from app.schemas.proposal import ProposalCreate, ProposalUpdate

class CRUDProposal(CRUDBase[ProposalModel, ProposalCreate, ProposalUpdate]):
    """
    Proposal-specific CRUD operations.
    """
    def _validate_request_for_proposal(self, db: Session, request_id: int) -> RequestModel:
        """
        Validates if a request is eligible for new proposals.
        Raises ValueError if not.
        """
        request = db.query(RequestModel).filter(RequestModel.id == request_id).first()
        if not request:
            raise ValueError("Request not found.")
        if request.status != RequestStatusEnum.APPROVED:
            raise ValueError(f"Proposals can only be submitted for 'APPROVED' requests. Current status: {request.status.value}")

        # Compare date part of expiration_date with current date part
        if request.expiration_date < datetime.utcnow().date():
            raise ValueError("Proposals cannot be submitted for expired requests.")
        return request

    def get_by_request_and_supplier(
        self, db: Session, *, request_id: int, supplier_id: int
    ) -> Optional[ProposalModel]:
        """
        Get a proposal by request ID and supplier ID (due to UniqueConstraint).
        """
        return db.query(ProposalModel).filter(
            ProposalModel.request_id == request_id,
            ProposalModel.supplier_id == supplier_id
        ).first()

    def create_with_supplier(
        self, db: Session, *, obj_in: ProposalCreate, supplier_id: int
    ) -> ProposalModel:
        """
        Create a new proposal, ensuring the associated request is valid for proposals
        and that the supplier hasn't already proposed.
        """
        # Validate the request first (raises ValueError if not valid)
        self._validate_request_for_proposal(db, request_id=obj_in.request_id)

        # Check for existing proposal from this supplier for this request
        existing_proposal = self.get_by_request_and_supplier(
            db, request_id=obj_in.request_id, supplier_id=supplier_id
        )
        if existing_proposal:
            raise ValueError("Supplier has already submitted a proposal for this request.")

        db_obj = ProposalModel(
            **obj_in.model_dump(), # Pydantic v2
            supplier_id=supplier_id,
            status=ProposalStatusEnum.SUBMITTED # Initial status for a new proposal
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        # Eager load supplier for the returned object, as it's often needed in response
        db.refresh(db_obj, attribute_names=['supplier'])
        return db_obj

    def get_multi_by_supplier(
        self, db: Session, *, supplier_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProposalModel]:
        """
        Get multiple proposals submitted by a specific supplier.
        Eager loads supplier and request details.
        """
        return (
            db.query(self.model)
            .filter(ProposalModel.supplier_id == supplier_id)
            .options(
                selectinload(ProposalModel.supplier),
                selectinload(ProposalModel.request) # Load the associated request
            )
            .order_by(ProposalModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_request(
        self, db: Session, *, request_id: int, skip: int = 0, limit: int = 100
    ) -> List[ProposalModel]:
        """
        Get multiple proposals for a specific request.
        Eager loads supplier details.
        """
        return (
            db.query(self.model)
            .filter(ProposalModel.request_id == request_id)
            .options(selectinload(ProposalModel.supplier)) # Load the supplier for each proposal
            .order_by(ProposalModel.created_at.asc()) # Show oldest proposals first for a request
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_supplier_and_request(self, db: Session, id: int) -> Optional[ProposalModel]:
        """
        Get a single proposal by its ID, with supplier and associated request (including request's owner)
        eagerly loaded.
        """
        return (
            db.query(self.model)
            .options(
                selectinload(ProposalModel.supplier),
                selectinload(ProposalModel.request).selectinload(RequestModel.owner) # Also load request's owner
            )
            .filter(self.model.id == id)
            .first()
        )

    def get_multi( # Overriding base get_multi for default eager loading
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ProposalModel]:
        """
        Default get_multi for proposals, loads supplier and request details.
        Useful for admin views of all proposals.
        """
        return (
            db.query(self.model)
            .options(
                selectinload(ProposalModel.supplier),
                selectinload(ProposalModel.request)
            )
            .order_by(ProposalModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

proposal = CRUDProposal(ProposalModel)
