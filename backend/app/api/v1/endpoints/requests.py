from typing import Any, List, Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app import crud, models, schemas
from backend.app.database import get_db
from backend.app.security.jwt import get_current_user
# Assuming User schema is available via schemas.User for current_user type hint
# from backend.app.schemas.user import User as UserSchema

router = APIRouter()

@router.post("/", response_model=schemas.Request, status_code=status.HTTP_201_CREATED)
def create_request(
    *,
    db: Annotated[Session, Depends(get_db)],
    request_in: schemas.RequestCreate,
    current_user: Annotated[models.User, Depends(get_current_user)] # Type hint with SQLAlchemy model
    # current_user: Annotated[UserSchema, Depends(get_current_user)] # Or Pydantic schema
) -> models.Request:
    """
    Create new request.
    Placeholder: End User role check.
    """
    # TODO: Implement role check: End User only
    # For now, any authenticated user can create a request.
    # current_user is now a models.User instance from get_current_user
    if not current_user:
        # This case should ideally be handled by get_current_user raising an exception
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # TODO: Implement role check: End User only
    # Example: if current_user.role != "end_user":
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only end users can create requests")

    created_request = crud.request.create_with_owner(db=db, obj_in=request_in, owner_id=current_user.id)
    return created_request

@router.get("/", response_model=List[schemas.Request])
def read_requests(
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: Annotated[models.User, Depends(get_current_user)] # Using model for consistency
) -> List[models.Request]:
    """
    Retrieve requests.
    TODO: Filter by owner or role (e.g., admin sees all, user sees own).
    """
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Example: Admin sees all, others see their own.
    # TODO: Refine role definitions and access control logic.
    if hasattr(current_user, 'role') and current_user.role == 'admin': # Ensure 'role' attribute exists
        requests = crud.request.get_multi(db, skip=skip, limit=limit)
    elif hasattr(current_user, 'id'): # Ensure 'id' attribute exists
        requests = crud.request.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    else:
        # This case should ideally not be reached if get_current_user works correctly
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User object misconfigured")
    return requests

@router.get("/{request_id}", response_model=schemas.Request)
def read_request(
    *,
    db: Annotated[Session, Depends(get_db)],
    request_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Request:
    """
    Get request by ID.
    TODO: Check ownership or admin role.
    """
    request = crud.request.get(db=db, id=request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Placeholder for ownership/role check
    if not (hasattr(current_user, 'id') and hasattr(current_user, 'role') and \
            (request.owner_id == current_user.id or current_user.role == "admin")):
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        pass # Soft pass for now, uncomment HTTPException for strict check
    return request

@router.put("/{request_id}", response_model=schemas.Request)
def update_request(
    *,
    db: Annotated[Session, Depends(get_db)],
    request_id: int,
    request_in: schemas.RequestUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Request:
    """
    Update a request.
    TODO: Check ownership or admin role.
    """
    request = crud.request.get(db=db, id=request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Placeholder for ownership/role check
    if not (hasattr(current_user, 'id') and hasattr(current_user, 'role') and \
            (request.owner_id == current_user.id or current_user.role == "admin")):
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        pass # Soft pass for now

    updated_request = crud.request.update(db=db, db_obj=request, obj_in=request_in)
    return updated_request

@router.delete("/{request_id}", response_model=schemas.Request) # Or perhaps just status_code=204
def delete_request(
    *,
    db: Annotated[Session, Depends(get_db)],
    request_id: int,
    current_user: Annotated[models.User, Depends(get_current_user)]
) -> models.Request:
    """
    Delete a request.
    TODO: Check ownership or admin role.
    """
    request = crud.request.get(db=db, id=request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Placeholder for ownership/role check
    # if request.owner_id != current_user.id and current_user.role != "admin":
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    deleted_request = crud.request.remove(db=db, id=request_id)
    if not deleted_request: # Should not happen if previous check passed
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found during deletion")
    return deleted_request
