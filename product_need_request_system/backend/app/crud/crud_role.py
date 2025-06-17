"""
CRUD operations for Role model.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.role import Role as RoleModel
from app.schemas.role import RoleCreate # RoleUpdate will be based on RoleCreate for now

# Define RoleUpdate. For simple cases, it can be the same as RoleCreate.
# If RoleUpdate needs different fields (e.g., some fields cannot be updated),
# it should be defined distinctly in schemas.role.
class RoleUpdate(RoleCreate):
    """
    Schema for updating a role. For now, assumes same fields as creation.
    If specific fields are not updatable, this should be a distinct schema.
    """
    pass

class CRUDRole(CRUDBase[RoleModel, RoleCreate, RoleUpdate]):
    """
    Role-specific CRUD operations.
    """
    def get_by_name(self, db: Session, *, name: str) -> Optional[RoleModel]:
        """
        Get a role by its name.

        Args:
            db: SQLAlchemy database session.
            name: Name of the role to search for.

        Returns:
            The RoleModel instance if found, else None.
        """
        return db.query(RoleModel).filter(RoleModel.name == name).first()

# Create a global instance of CRUDRole for easy import and use
role = CRUDRole(RoleModel)
