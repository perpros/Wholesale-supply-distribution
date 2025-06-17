"""
Celery tasks related to Request lifecycle management.

Includes tasks for:
- Automatically expiring requests past their expiration_date.
- Automatically closing EXPIRED requests based on whether their need was met.
"""
from celery import shared_task # Use shared_task for tasks that don't depend on a specific Celery app instance
from sqlalchemy.orm import Session
from datetime import date # Use date for comparing with expiration_date which is a Date type
import logging

from app.db.session import SessionLocal # To create a DB session for tasks
from app import crud, models # For accessing Request model and CRUD operations
from app.models.enums import RequestStatusEnum
from app.services.request_service import request_service # For "need met" business logic

# Configure a logger for tasks module, if not configured globally
logger = logging.getLogger(__name__)

@shared_task(name="tasks.auto_expire_requests_task")
def auto_expire_requests_task() -> str:
    """
    Periodically checks for requests whose expiration_date has passed
    and updates their status to EXPIRED.
    This task should be run by the Celery beat scheduler.
    """
    db: Session = SessionLocal()
    updated_count = 0
    processed_count = 0
    try:
        # Filter for requests that are past their expiration_date
        # and are in a status that allows them to be expired (e.g., SUBMITTED, APPROVED).
        expirable_statuses = [RequestStatusEnum.SUBMITTED, RequestStatusEnum.APPROVED]

        # Query for requests to expire
        # Ensure comparison is between date objects if expiration_date is stored as Date
        requests_to_expire = (
            db.query(models.Request)
            .filter(
                models.Request.expiration_date < date.today(),
                models.Request.status.in_(expirable_statuses)
            )
            .all()
        )
        processed_count = len(requests_to_expire)

        if not requests_to_expire:
            return f"No requests found needing expiration. Processed {processed_count}."

        for req in requests_to_expire:
            try:
                crud.request.update_status(
                    db,
                    db_obj=req,
                    new_status=RequestStatusEnum.EXPIRED,
                    user_id=None, # System action, no specific user initiated
                    notes="Request automatically expired due to passing expiration date."
                )
                updated_count += 1
            except Exception as e_inner:
                logger.error(f"Error expiring request ID {req.id}: {str(e_inner)}")
                # Decide if one failure should rollback all; typically not for batch jobs.
                # Individual errors are logged; transaction continues for other requests.

        db.commit() # Commit all successful status updates for this batch
        return f"Processed {processed_count} requests for expiration. {updated_count} updated successfully."
    except Exception as e_outer:
        db.rollback() # Rollback in case of a broader issue during query or setup
        logger.error(f"Major error during request expiration task: {str(e_outer)}")
        return f"Error during request expiration task: {str(e_outer)}"
    finally:
        db.close()

@shared_task(name="tasks.auto_close_requests_task")
def auto_close_requests_task() -> str:
    """
    Periodically checks EXPIRED requests and attempts to auto-close them.
    - If "Need met" (based on proposal quantities), status changes to CLOSED_FULFILLED.
    - If "Need not met", status changes to CLOSED_UNFULFILLED.
    This task should be run by the Celery beat scheduler.
    """
    db: Session = SessionLocal()
    closed_fulfilled_count = 0
    closed_unfulfilled_count = 0
    processed_count = 0
    try:
        # Get all requests currently in EXPIRED status
        expired_requests = (
            db.query(models.Request)
            .filter(models.Request.status == RequestStatusEnum.EXPIRED)
            .all()
        )
        processed_count = len(expired_requests)

        if not expired_requests:
            return f"No EXPIRED requests found for auto-closure. Processed {processed_count}."

        for req in expired_requests:
            try:
                need_met = request_service.is_request_need_met(db, request_id=req.id)
                new_status: RequestStatusEnum
                notes: str

                if need_met:
                    new_status = RequestStatusEnum.CLOSED_FULFILLED
                    notes = "Request auto-closed: Need considered fulfilled based on proposals."
                    closed_fulfilled_count += 1
                else:
                    new_status = RequestStatusEnum.CLOSED_UNFULFILLED
                    notes = "Request auto-closed: Need considered not fulfilled based on proposals."
                    closed_unfulfilled_count += 1

                crud.request.update_status(
                    db,
                    db_obj=req,
                    new_status=new_status,
                    user_id=None, # System action
                    notes=notes
                )
            except Exception as e_inner:
                logger.error(f"Error auto-closing request ID {req.id}: {str(e_inner)}")
                # Log individual errors; transaction continues for other requests.

        db.commit() # Commit all successful status updates for this batch
        return (
            f"Processed {processed_count} EXPIRED requests for auto-closure. "
            f"{closed_fulfilled_count} closed as fulfilled, "
            f"{closed_unfulfilled_count} closed as unfulfilled."
        )
    except Exception as e_outer:
        db.rollback() # Rollback in case of a broader issue
        logger.error(f"Major error during request auto-closure task: {str(e_outer)}")
        return f"Error during request auto-closure task: {str(e_outer)}"
    finally:
        db.close()
