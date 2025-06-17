"""User model definition."""
from sqlalchemy import Column, Integer, String, Boolean # Table and ForeignKey removed as they are not directly used
from sqlalchemy.orm import relationship
from .base import Base
from .role import user_role_association

# Import forward references for relationships to avoid circular import issues
# These are strings, and SQLAlchemy resolves them.
# For type hinting and editor support, actual imports can be problematic with circular dependencies.
# String-based forward references (e.g., relationship("Request", ...)) are used to avoid these issues.

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): Primary key for the user.
        email (str): Unique email address of the user.
        hashed_password (str): Hashed password for the user.
        full_name (str, optional): Full name of the user.
        is_active (bool): Flag to indicate if the user account is active. Defaults to True.
        roles (relationship): Many-to-many relationship with Role model.
        requests (relationship): One-to-many relationship with Request model (user as owner).
        proposals (relationship): One-to-many relationship with Proposal model (user as supplier).
        status_changes (relationship): One-to-many relationship with RequestStatusHistory model (user as changer).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    roles = relationship(
        "Role",
        secondary=user_role_association,
        back_populates="users"
    )

    # New relationships
    # Using string literals for class names to handle forward references gracefully
    requests = relationship("Request", back_populates="owner", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="supplier", cascade="all, delete-orphan")
    status_changes = relationship("RequestStatusHistory", back_populates="changed_by")

    def __repr__(self):
        """String representation of the User object."""
        return f"<User(email='{self.email}')>"
