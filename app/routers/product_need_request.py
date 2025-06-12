from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app import schemas # This will now also pick up ProductNeedRequestSuccessResponse
from app import crud
from app.db.session import get_db
from app.core.security import get_current_active_user # Ensure this is correctly imported

router = APIRouter()

@router.post(
    "/product-need-request",
    response_model=schemas.product_need_request.ProductNeedRequestSuccessResponse, # Updated response_model
    status_code=status.HTTP_201_CREATED,
    summary="Create a product need request",
    response_description="ProductNeedRequest successfully submitted",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Validation failed due to invalid input data. This can include issues like dates not being in the future, expiration date not being after promised date, or missing required fields."},
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated. Authentication token is missing or invalid."},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized. The authenticated user does not have permission to perform this action (e.g., user is inactive)."},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error. The request body is syntactically correct but semantically incorrect (e.g. date validation failed)."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error. An unexpected error occurred on the server."},
    }
)
def create_request(
    *,
    db: Session = Depends(get_db),
    request_in: schemas.product_need_request.ProductNeedRequestCreate,
    current_user: Any = Depends(get_current_active_user) # Uncommented and assuming User model from security
) -> schemas.product_need_request.ProductNeedRequestSuccessResponse: # Return type annotation updated
    """
    Create a new product need request. Requires authentication.

    - **product_type**: Type of the product (e.g., "Laptop", "Monitor").
    - **product_count**: Number of products needed (must be > 0).
    - **promised_delivery_date**: Date by which products are promised (YYYY-MM-DD, must be in the future).
    - **expiration_date**: Date after which the request is no longer valid (YYYY-MM-DD, must be after promised_delivery_date).
    """
    # Pydantic validation for request_in happens automatically.
    # Date logic validators are in schemas.product_need_request.ProductNeedRequestCreate
    # If those validators raise ValueError, FastAPI by default converts it to a 422 response.
    # The custom exception handler for ValueError added previously is no longer in this version of the script,
    # relying on FastAPI's default handling for Pydantic's ValueError.

    try:
        created_request = crud.crud_product_need_request.create_product_need_request(db=db, request_in=request_in)
    except ValueError as ve: # Specifically catch ValueErrors from CRUD or deeper logic if any
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, # Or 400 depending on interpretation
            detail=str(ve)
        )
    except Exception as e:
        # In a real app, log the exception e with more details
        # print(f"Error during request creation: {e}") # For debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating the request.",
        )

    return schemas.product_need_request.ProductNeedRequestSuccessResponse(
        message="ProductNeedRequest successfully submitted",
        id=created_request.id
    )
