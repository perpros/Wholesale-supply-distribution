"""
Celery Application Configuration.

Initializes and configures the Celery application instance, which will be used
by Celery workers to discover and execute tasks.
"""
from celery import Celery
from app.core.config import settings # Import the global settings instance

# Initialize Celery
# The first argument is conventionally the name of the current module,
# but can be any name. It's used for auto-generating task names if not specified.
# `broker` and `backend` URLs are sourced from the application settings.
# `include` lists modules where tasks are defined, so the worker can find them.
celery_app = Celery(
    "worker", # Name of the Celery application (often corresponds to the worker process name)
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        'app.tasks.request_tasks' # Module(s) containing task definitions
    ]
)

# Optional Celery configuration settings
# These can be fine-tuned based on application needs.
celery_app.conf.update(
    task_serializer='json',        # Use JSON for task serialization
    accept_content=['json'],       # Accept only JSON content
    result_serializer='json',      # Use JSON for result serialization
    timezone='UTC',                # Standardize on UTC for timezones
    enable_utc=True,               # Ensure Celery uses UTC consistently

    # task_track_started=True,     # Uncomment to track when tasks begin execution
    # worker_prefetch_multiplier=1,  # Can be useful for long-running tasks to prevent worker saturation
    # task_acks_late=True,         # Tasks acknowledged after completion; useful if tasks are idempotent
                                   # and can be safely retried on worker failure.
    # broker_connection_retry_on_startup=True, # Attempt to retry broker connection on startup
)

# Example: Define a beat schedule (periodic tasks) programmatically
# This schedule will be used if the Celery beat scheduler is run with this app instance.
# Alternatively, schedules can be managed via Django admin (django-celery-beat) or other means.
# celery_app.conf.beat_schedule = {
#     'auto-expire-requests-hourly': {
#         'task': 'app.tasks.request_tasks.auto_expire_requests_task', # Name of the task as registered
#         'schedule': 3600.0,  # Run every hour (time in seconds)
#         # 'args': (arg1, arg2), # Optional arguments for the task
#     },
#     'auto-close-requests-hourly': {
#         'task': 'app.tasks.request_tasks.auto_close_requests_task',
#         'schedule': 3600.0, # Run every hour
#     },
# }

# To run worker: celery -A app.core.celery_app worker -l info
# To run beat:   celery -A app.core.celery_app beat -l info
# Ensure Redis server is running.
