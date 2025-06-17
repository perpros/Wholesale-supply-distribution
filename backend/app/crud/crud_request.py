from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.crud.crud_base import CRUDBase
from backend.app.models.request import Request
from backend.app.schemas.request import RequestCreate, RequestUpdate

class CRUDRequest(CRUDBase[Request, RequestCreate, RequestUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: RequestCreate, owner_id: int
    ) -> Request:
        db_obj = Request(
            **obj_in.model_dump(), # Pydantic V2
            # **obj_in.dict(), # Pydantic V1
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Request]:
        return (
            db.query(self.model)
            .filter(Request.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

# Instantiate the CRUDRequest class
request = CRUDRequest(Request)
