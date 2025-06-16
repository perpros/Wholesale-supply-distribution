from sqlalchemy import Column, Integer, String, Enum as SQLAlchemyEnum, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import Base, UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    requests = relationship("Request", back_populates="requester")
    proposals = relationship("Proposal", back_populates="supplier")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role.value}')>"
