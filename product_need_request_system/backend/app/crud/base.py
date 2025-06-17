"""
Generic Base Class for CRUD operations.

Provides a template for Create, Read, Update, and Delete operations
that can be inherited by specific CRUD classes for different models.
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Assuming your SQLAlchemy Base is defined in app.models.base
# If it's elsewhere, adjust the import path accordingly.
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for CRUD operations on a SQLAlchemy model.

    Methods:
    - get: Retrieve a single record by ID.
    - get_multi: Retrieve multiple records with optional skip and limit.
    - create: Create a new record.
    - update: Update an existing record.
    - remove: Delete a record by ID.
    """
    def __init__(self, model: Type[ModelType]):
        """
        Initialize the CRUDBase with a SQLAlchemy model.

        Args:
            model: The SQLAlchemy model class this CRUD object will operate on.
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by its ID.

        Args:
            db: SQLAlchemy database session.
            id: The ID of the record to retrieve.

        Returns:
            The model instance if found, else None.
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records, with pagination support.

        Args:
            db: SQLAlchemy database session.
            skip: Number of records to skip (for pagination).
            limit: Maximum number of records to return.

        Returns:
            A list of model instances.
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record in the database.

        Args:
            db: SQLAlchemy database session.
            obj_in: Pydantic schema containing the data for the new record.

        Returns:
            The newly created model instance.
        """
        # Convert Pydantic model to a dictionary suitable for SQLAlchemy model instantiation
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore[call-arg] # Ignoring mypy error due to dynamic **obj_in_data
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record in the database.

        Args:
            db: SQLAlchemy database session.
            db_obj: The existing model instance to update.
            obj_in: Pydantic schema or dictionary containing the update data.
                    Uses `model_dump(exclude_unset=True)` for Pydantic v2 to only update provided fields.

        Returns:
            The updated model instance.
        """
        obj_data = jsonable_encoder(db_obj) # Current state of db_obj as dict
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # For Pydantic v2, use model_dump. For v1, use dict.
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data: # Iterate over fields in the existing db_obj's dict representation
            if field in update_data: # Check if the field is present in the update data
                setattr(db_obj, field, update_data[field]) # If so, update the attribute on the db_obj

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Remove a record from the database by its ID.

        Args:
            db: SQLAlchemy database session.
            id: The ID of the record to delete.

        Returns:
            The deleted model instance if found and deleted, else None.
        """
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

# Example usage (not part of the class itself):
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate
# item_crud = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
