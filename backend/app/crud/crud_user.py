from typing import Optional
from sqlalchemy.orm import Session

from backend.app.crud.crud_base import CRUDBase
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate # UserUpdate can be basic BaseModel if not specific
from backend.app.security.hashing import Hasher # For password hashing

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=Hasher.get_password_hash(obj_in.password),
            role=obj_in.role if obj_in.role else "user", # Ensure role has a default
            is_active=True # Default to active, or make it part of UserCreate schema
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: UserUpdate # type: ignore -> UserUpdate might not be fully defined yet
    ) -> User:
        # If obj_in contains a password, hash it before updating
        if isinstance(obj_in, dict) and obj_in.get("password"):
            obj_in["hashed_password"] = Hasher.get_password_hash(obj_in["password"])
            del obj_in["password"]
        elif hasattr(obj_in, "password") and obj_in.password:
            obj_in.hashed_password = Hasher.get_password_hash(obj_in.password) # type: ignore
            delattr(obj_in, "password")

        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    # Add other user-specific CRUD methods if needed, e.g., activate/deactivate user

# Instantiate the CRUDUser class
user = CRUDUser(User)
