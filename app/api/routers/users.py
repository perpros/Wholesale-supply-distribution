from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import user_service
from app.models.user import User as UserModel
from app.core.security import get_current_user
from app.core.permissions import require_admin_role # Import new dependency
from app.core.config import settings

router = APIRouter(prefix=f"{settings.API_V1_STR}/users", tags=["Users"])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    # current_admin: UserModel = Depends(require_admin_role) # Protect user creation by Admin only
    # For now, let's keep it open as per original setup, then discuss if it should be admin-only
    # If open, any authenticated user can create another user, which might not be desired.
    # Based on typical system design, user creation (especially with roles) is an admin task.
    # Let's assume it should be admin only for now.
    admin_user: UserModel = Depends(require_admin_role) # User creating others must be admin
):
    db_user = user_service.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Ensure only admins can create other admins, or set roles appropriately.
    # For now, UserCreate schema takes a role, which an Admin would specify.
    created_user = user_service.create_user(db=db, user_in=user_in)
    return created_user

@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: UserModel = Depends(get_current_user) # Any authenticated user can see their own profile
):
    return current_user

@router.get("/", response_model=List[UserRead])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin_role) # Only admin can list all users
):
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserRead)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: UserModel = Depends(require_admin_role) # Only admin can fetch any user by ID
    # If users should see their own profile via this endpoint:
    # current_user: UserModel = Depends(get_current_user)
    # then check if current_user.id == user_id or current_user.role == UserRole.ADMIN
):
    user = user_service.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    # If not admin_user dependency, add check:
    # if admin_user.id != user_id and admin_user.role != UserRole.ADMIN: # (assuming admin_user is current_user here)
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return user
