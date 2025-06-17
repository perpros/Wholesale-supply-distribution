"""Role model definition."""
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

# Association table for User and Role many-to-many relationship
user_role_association = Table(
    'user_role_association', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class Role(Base):
    """
    Represents a role that can be assigned to a user.

    Attributes:
        id (int): Primary key for the role.
        name (str): Unique name of the role (e.g., "admin", "editor").
        description (str, optional): A brief description of the role.
        users (relationship): Many-to-many relationship with User model.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)

    users = relationship(
        "User",
        secondary=user_role_association,
        back_populates="roles"
    )

    def __repr__(self):
        """String representation of the Role object."""
        return f"<Role(name='{self.name}')>"
