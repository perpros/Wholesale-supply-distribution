"""
CRUD operations for User model.

Extends CRUDBase with user-specific methods like password hashing during creation,
email-based lookup, and authentication.
"""
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session, joinedload

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate
from app.crud.crud_role import role as crud_role # Import role CRUD

class CRUDUser(CRUDBase[UserModel, UserCreate, UserUpdate]):
    """
    User-specific CRUD operations.
    """
    def get_by_email(self, db: Session, *, email: str) -> Optional[UserModel]:
        """
        Get a user by their email address, with roles eagerly loaded.

        Args:
            db: SQLAlchemy database session.
            email: Email address to search for.

        Returns:
            The UserModel instance if found (with roles populated), else None.
        """
        return db.query(UserModel).options(joinedload(UserModel.roles)).filter(UserModel.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserModel:

        Args:
            db: SQLAlchemy database session.
            email: Email address to search for.

        Returns:
            The UserModel instance if found, else None.
        """
        return db.query(UserModel).filter(UserModel.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> UserModel:
        """
        Create a new user, hashing the password before storage.

        Args:
            db: SQLAlchemy database session.
            obj_in: Pydantic schema (UserCreate) with new user data.

        Returns:
            The newly created UserModel instance.
        """
        db_obj = UserModel(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_active=obj_in.is_active if obj_in.is_active is not None else True
        )

        # Assign a default role, e.g., "End User"
        default_role_name = "End User"
        end_user_role = crud_role.get_by_name(db, name=default_role_name)
        if end_user_role:
            db_obj.roles.append(end_user_role)
        else:
            # Strategy: Log a warning if the default role is not found.
            # In a production system, this might need stricter handling (e.g., raise error, ensure role seeding).
            print(f"Warning: Default role '{default_role_name}' not found. User '{obj_in.email}' created without it.")
            # Consider: raise ValueError(f"Default role '{default_role_name}' not found. Cannot create user.")

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        # Eagerly load roles for the returned object to ensure they are available in the response
        db.refresh(db_obj, attribute_names=['roles'])
        return db_obj

    def update(
        self, db: Session, *, db_obj: UserModel, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> UserModel:
        """
        Update an existing user. If 'password' is in obj_in, it will be hashed.

        Args:
            db: SQLAlchemy database session.
            db_obj: The existing UserModel instance to update.
            obj_in: Pydantic schema (UserUpdate) or dict with update data.

        Returns:
            The updated UserModel instance.
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) # Pydantic v2

        # If password is being updated, hash it before saving
        if "password" in update_data and update_data["password"] is not None:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"] # Remove plain password from update_data
        else:
            # Ensure 'password' key does not proceed if it's None or not present
            if "password" in update_data:
                del update_data["password"]


        # Use super().update() with the modified update_data
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[UserModel]:
        """
        Authenticate a user by email and password.

        Args:
            db: SQLAlchemy database session.
            email: User's email.
            password: User's plain text password.

        Returns:
            The UserModel instance if authentication is successful, else None.
        """
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

# Create a global instance of CRUDUser for easy import and use
user = CRUDUser(UserModel)
