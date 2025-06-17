from sqlalchemy.orm import Session
# Passlib context and functions are now in security.py
from typing import Optional

from . import models, schemas
from .schemas import RequestStatus # For direct use of Enum
from . import security # Import security to use its get_password_hash

# User CRUD operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password) # Use security.get_password_hash
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password,
        role=user.role.value # Ensure Enum value is passed if role is an Enum in model
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- RequestStatusHistory CRUD operations ---
def create_request_status_change(db: Session, request_id: int, new_status: schemas.RequestStatus, changed_by_user_id: Optional[int]) -> models.RequestStatusHistory:
    db_status_change = models.RequestStatusHistory(
        request_id=request_id,
        status=new_status.value, # Store the string value of the enum
        changed_by_user_id=changed_by_user_id
    )
    db.add(db_status_change)
    db.commit()
    db.refresh(db_status_change)
    return db_status_change

# --- Request CRUD operations ---
def create_request(db: Session, request: schemas.RequestCreate, user_id: int) -> models.Request:
    db_request = models.Request(
        **request.model_dump(),
        user_id=user_id,
        status=schemas.RequestStatus.SUBMITTED.value # Initial status
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    # Log initial status change
    create_request_status_change(
        db=db,
        request_id=db_request.id,
        new_status=schemas.RequestStatus.SUBMITTED, # Pass the enum member
        changed_by_user_id=user_id
    )
    return db_request

def get_request(db: Session, request_id: int) -> Optional[models.Request]:
    return db.query(models.Request).filter(models.Request.id == request_id).first()

def get_requests_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[models.Request]:
    return db.query(models.Request).filter(models.Request.user_id == user_id).offset(skip).limit(limit).all()

def get_all_requests(db: Session, skip: int = 0, limit: int = 100, status: Optional[schemas.RequestStatus] = None) -> list[models.Request]:
    query = db.query(models.Request)
    if status:
        query = query.filter(models.Request.status == status.value)
    return query.offset(skip).limit(limit).all()

def update_request_status(db: Session, db_request: models.Request, new_status: schemas.RequestStatus, changed_by_user_id: Optional[int]) -> models.Request:
    db_request.status = new_status.value
    db.add(db_request) # SQLAlchemy tracks changes, explicit add is fine
    db.commit()
    db.refresh(db_request)
    create_request_status_change(
        db=db,
        request_id=db_request.id,
        new_status=new_status, # Pass the enum member
        changed_by_user_id=changed_by_user_id
    )
    return db_request

def update_request_details(db: Session, db_request: models.Request, request_update: schemas.RequestUpdate) -> models.Request:
    update_data = request_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_request, key, value)
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    # Optional: could add a RequestStatusHistory entry for "details_updated"
    # For now, not changing status directly here, so no specific log for that.
    # If auditing detail changes is required, a different mechanism or a generic log might be used.
    return db_request


# --- Proposal CRUD operations ---
def create_proposal(db: Session, proposal: schemas.ProposalCreate, request_id: int, supplier_id: int) -> models.Proposal:
    # proposal.request_id is now part of ProposalCreate schema, but we use the path parameter for consistency
    db_proposal = models.Proposal(
        quantity=proposal.quantity,
        request_id=request_id,
        supplier_id=supplier_id
    )
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def get_proposal(db: Session, proposal_id: int) -> Optional[models.Proposal]:
    return db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()

def get_proposals_by_request(db: Session, request_id: int, skip: int = 0, limit: int = 100) -> list[models.Proposal]:
    return db.query(models.Proposal).filter(models.Proposal.request_id == request_id).offset(skip).limit(limit).all()

def get_proposals_by_supplier(db: Session, supplier_id: int, skip: int = 0, limit: int = 100) -> list[models.Proposal]:
    return db.query(models.Proposal).filter(models.Proposal.supplier_id == supplier_id).offset(skip).limit(limit).all()

def get_proposal_by_request_and_supplier(db: Session, request_id: int, supplier_id: int) -> Optional[models.Proposal]:
    return db.query(models.Proposal).filter(
        models.Proposal.request_id == request_id,
        models.Proposal.supplier_id == supplier_id
    ).first()

def update_proposal_quantity(db: Session, db_proposal: models.Proposal, quantity: int) -> models.Proposal:
    db_proposal.quantity = quantity
    db.add(db_proposal)
    db.commit()
    db.refresh(db_proposal)
    return db_proposal

def delete_proposal(db: Session, db_proposal: models.Proposal) -> models.Proposal: # Return deleted obj or None
    db.delete(db_proposal)
    db.commit()
    # db_proposal object is now detached and its state is undefined after commit if not expired.
    # Depending on ORM config, accessing attributes might trigger new queries or errors.
    # For DELETE, typically nothing is returned or a confirmation.
    # Returning the object might be misleading as it's no longer in DB.
    return db_proposal # Or return None, or simply nothing (caller handles based on no exception)

# Placeholder for Notification CRUD
