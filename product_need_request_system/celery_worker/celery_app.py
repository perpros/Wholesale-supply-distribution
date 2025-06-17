from celery import Celery
from celery.schedules import crontab # For scheduling

# TODO: Configure REDIS_URL from environment variable
REDIS_URL = "redis://localhost:6379/0" # Default Redis URL

celery_app = Celery(
    "product_need_request_system_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["celery_worker.tasks"] # Points to the tasks module relative to celery_worker package
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ensure tasks accept json
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Celery Beat Schedule
    # This schedule configures Celery Beat to run tasks periodically.
    # Celery Beat needs to be run as a separate process.
    beat_schedule={
        'auto-expire-requests-daily': {
            'task': 'celery_worker.tasks.auto_expire_requests_task', # Name of the task
            'schedule': crontab(hour=1, minute=0),  # Run daily at 1:00 AM UTC
            # 'args': (arg1, arg2), # If your task takes arguments
        },
        'auto-close-requests-daily': {
            'task': 'celery_worker.tasks.auto_close_requests_task',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM UTC
        },
    }
)

# Optional: If tasks need access to FastAPI app's settings or DB directly
# This is one way, another is to initialize DB session within each task as done in tasks.py
# from app.database import SessionLocal # Assuming app is in PYTHONPATH
# celery_app.conf.SQLAlchemySessionLocal = SessionLocal

# To run the worker:
# poetry run celery -A celery_worker.celery_app worker -l info
# To run the beat scheduler:
# poetry run celery -A celery_worker.celery_app beat -l info

# Ensure that the main project directory is in PYTHONPATH when running celery,
# or that celery_worker is structured such that 'app' can be imported.
# Running with `poetry run` from the project root usually handles this.
