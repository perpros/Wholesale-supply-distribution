import os
from celery import Celery
from backend.app.core.config import settings

# It's a common practice to set the default Django settings module for 'celery' programs.
# This is not strictly necessary if you're not using Django but can be helpful if your project structure
# or some libraries expect it. For a pure FastAPI app, this might not be needed.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings') # Example if using Django

# Create Celery instance
# The first argument to Celery is the name of the current module.
# This is only needed so that names can be automatically generated when tasks are defined in the __main__ module.
celery_app = Celery(
    "worker", # Typically the name of the main module where tasks are defined or a generic name
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.app.tasks.example_tasks"] # Explicitly include task modules
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # You can add more Celery settings here if needed
    # For example, to route tasks to different queues:
    # task_routes = {
    #     'backend.app.tasks.example_tasks.example_task': {'queue': 'hipri'},
    # },
)

# Autodiscover tasks: Celery will look for a tasks.py file in all installed apps.
# For FastAPI, it's common to list the modules where tasks are defined.
# The `include` parameter in Celery() constructor is often preferred for FastAPI.
# If you use autodiscover_tasks, ensure your tasks are in modules that Celery can find.
# e.g., celery_app.autodiscover_tasks(["backend.app.tasks"])
# If `include` is used in Celery constructor, autodiscover_tasks might be redundant or provide alternative way.

# How to run the Celery worker (example for development):
# Ensure your Python path is set up correctly so Celery can find your app module.
# From the project root directory (where your `backend` folder is):
# celery -A backend.app.core.celery_app worker -l info -P eventlet # For Windows or when gevent/eventlet is preferred
# celery -A backend.app.core.celery_app worker -l info # For Linux/MacOS

if __name__ == "__main__":
    # This is for running the worker directly using `python -m backend.app.core.celery_app worker ...`
    # Though `celery -A ...` command is more common.
    celery_app.start()
