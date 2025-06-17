from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.crud.crud_base import CRUDBase
from backend.app.models.proposal import Proposal
from backend.app.schemas.proposal import ProposalCreate, ProposalUpdate

class CRUDProposal(CRUDBase[Proposal, ProposalCreate, ProposalUpdate]):
    def create_with_supplier_and_request(
        self, db: Session, *, obj_in: ProposalCreate, supplier_id: int # request_id is in obj_in
    ) -> Proposal:
        db_obj = Proposal(
            **obj_in.model_dump(), # Pydantic V2
            # **obj_in.dict(), # Pydantic V1
            supplier_id=supplier_id
            # request_id is part of obj_in (ProposalCreate schema)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_request(
        self, db: Session, *, request_id: int, skip: int = 0, limit: int = 100
    ) -> List[Proposal]:
        return (
            db.query(self.model)
            .filter(Proposal.request_id == request_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_by_supplier(
        self, db: Session, *, supplier_id: int, skip: int = 0, limit: int = 100
    ) -> List[Proposal]:
        return (
            db.query(self.model)
            .filter(Proposal.supplier_id == supplier_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

# Instantiate the CRUDProposal class
proposal = CRUDProposal(Proposal)
