from .celery_app import celery_app
from app.database import SessionLocal # To create DB sessions for tasks
from app import models, schemas, crud # To interact with DB and use CRUD functions
from sqlalchemy.orm import Session
from sqlalchemy import func # For sum()
from datetime import date # For date comparisons
import logging # For logging task activity

# Configure a logger for tasks
logger = logging.getLogger(__name__)

def get_db_session_for_task() -> Session:
    # Helper to get a DB session for a task
    return SessionLocal()

@celery_app.task(name="celery_worker.tasks.auto_expire_requests_task")
def auto_expire_requests_task():
    logger.info("Starting auto_expire_requests_task...")
    db: Session = get_db_session_for_task()
    try:
        today = date.today()
        # Find requests that are not yet expired/closed/cancelled and whose expiration_date has passed
        requests_to_expire = db.query(models.Request).filter(
            models.Request.expiration_date < today,
            models.Request.status.notin_([
                schemas.RequestStatus.EXPIRED.value,
                schemas.RequestStatus.CLOSED.value,
                schemas.RequestStatus.CANCELLED.value
            ])
        ).all()

        expired_count = 0
        for req in requests_to_expire:
            logger.info(f"Expiring request ID {req.id} with expiration date {req.expiration_date}")
            # crud.update_request_status commits its own session changes.
            # This is acceptable for this task, but for high-volume batch operations,
            # one might modify CRUD functions to optionally not commit,
            # and then commit once at the end of the task.
            crud.update_request_status(db, db_request=req, new_status=schemas.RequestStatus.EXPIRED, changed_by_user_id=None)
            expired_count += 1

        # If crud.update_request_status does not commit, uncomment the line below.
        # Based on current crud implementation, it does commit.
        # db.commit()

        logger.info(f"Auto-expired {expired_count} requests.")
        return f"Expired {expired_count} requests."
    except Exception as e:
        logger.error(f"Error during request auto-expiration: {str(e)}", exc_info=True)
        db.rollback() # Rollback in case of error if operations were not committed by CRUD
        return f"Error during request expiration: {str(e)}"
    finally:
        db.close()

@celery_app.task(name="celery_worker.tasks.auto_close_requests_task")
def auto_close_requests_task():
    logger.info("Starting auto_close_requests_task...")
    db: Session = get_db_session_for_task()
    try:
        # Find requests that are 'approved' or 'expired' (as per typical business logic for closure)
        # and where the need might have been met or is no longer relevant.
        # For this task, focusing on 'expired' requests where need is met.
        # Or, requests that are 'approved' and past their delivery date + grace period (more complex logic not in spec)

        requests_to_check_for_closure = db.query(models.Request).filter(
            models.Request.status == schemas.RequestStatus.EXPIRED.value
            # Optionally, could also include APPROVED requests past delivery date by a certain margin
            # or models.Request.status == schemas.RequestStatus.APPROVED.value
        ).all()

        closed_count = 0
        for req in requests_to_check_for_closure:
            # Only consider closing if the request is currently 'expired'
            if req.status == schemas.RequestStatus.EXPIRED.value:
                total_proposal_quantity = db.query(func.sum(models.Proposal.quantity)).filter(
                    models.Proposal.request_id == req.id
                ).scalar() or 0

                if total_proposal_quantity >= req.quantity:
                    logger.info(f"Closing EXPIRED request ID {req.id} as need met. Quantity: {req.quantity}, Proposed: {total_proposal_quantity}")
                    crud.update_request_status(db, db_request=req, new_status=schemas.RequestStatus.CLOSED, changed_by_user_id=None)
                    closed_count += 1
                else:
                    logger.info(f"EXPIRED request ID {req.id} need not met. Quantity: {req.quantity}, Proposed: {total_proposal_quantity}. Stays EXPIRED.")

            # Add logic here if also considering APPROVED requests for closure
            # Example: if req.status == schemas.RequestStatus.APPROVED.value and req.promised_delivery_date < some_past_date:
            #   ... check proposal quantities ...
            #   crud.update_request_status(db, db_request=req, new_status=schemas.RequestStatus.CLOSED, changed_by_user_id=None)

        # db.commit() # if crud functions don't commit. They do.

        logger.info(f"Auto-closed {closed_count} requests where need was met.")
        return f"Closed {closed_count} requests where need was met."
    except Exception as e:
        logger.error(f"Error during request auto-closure: {str(e)}", exc_info=True)
        db.rollback()
        return f"Error during request auto-closure: {str(e)}"
    finally:
        db.close()
