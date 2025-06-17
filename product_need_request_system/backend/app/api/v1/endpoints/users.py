"""
API Endpoints for User Management.

Provides endpoints for:
- User registration (create_user).
- Retrieving current user's information (read_user_me).
- Updating current user's information (update_user_me).
- (Future/Admin) Listing users and retrieving specific users by ID.
"""
from typing import Any, List # List for potential future admin endpoints

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, models, schemas # models for type hinting UserModel, schemas for I/O
from app.api import deps # For dependencies like get_db, get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate, # UserCreate schema for input
) -> Any:
    """
    Create a new user.

    This endpoint registers a new user in the system.
    A default role (e.g., "End User") is assigned upon creation.
    If a user with the same email already exists, a 400 error is returned.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    try:
        # crud.user.create now handles default role assignment
        user = crud.user.create(db, obj_in=user_in)
    except ValueError as e:
        # Catch ValueError if crud.user.create raises it (e.g., default role not found and configured to raise)
        # This depends on the error handling strategy in crud_user.create.
        # If it only prints a warning, this try-except might not be strictly necessary here for that specific case.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}" # Provide more context if possible
        )
    return user

@router.get("/me", response_model=schemas.User)
def read_user_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current authenticated user's details.

    Requires a valid access token. Returns the data for the user
    associated with the token.
    """
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserUpdate, # UserUpdate schema for input
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update current authenticated user's details.

    Allows the authenticated user to update their own information (e.g., full_name, password).
    Email updates require checking for conflicts with other users.
    """
    # Handle email updates: if email is provided and different from current
    if user_in.email and user_in.email != current_user.email:
        existing_user = crud.user.get_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another user."
            )

    # The crud.user.update method handles password hashing if a new password is provided.
    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user

# --- Placeholder Admin Endpoints ---
# These are examples and would require RoleChecker dependency for admin access.

# @router.get("/", response_model=List[schemas.User], dependencies=[Depends(deps.RoleChecker(["Admin"]))])
# def read_users(
#     db: Session = Depends(deps.get_db),
#     skip: int = 0,
#     limit: int = 100,
# ) -> Any:
#     """
#     Retrieve a list of users. (Admin access required)
#     """
#     users = crud.user.get_multi(db, skip=skip, limit=limit)
#     return users

# @router.get("/{user_id}", response_model=schemas.User, dependencies=[Depends(deps.RoleChecker(["Admin"]))])
# def read_user_by_id(
#     user_id: int,
#     db: Session = Depends(deps.get_db),
# ) -> Any:
#     """
#     Get a specific user by their ID. (Admin access required)
#     """
#     user = crud.user.get(db, id=user_id)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#     # Add role check here if non-admins should not access arbitrary users,
#     # or if they should only access users within their organization, etc.
#     return user
