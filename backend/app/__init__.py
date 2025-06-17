# This makes 'app' a package.
# Expose Celery app instance for convenience or if needed by other parts of the application.
from .core.celery_app import celery_app

# You could also expose other central components here if desired, for example:
# from .database import Base, engine, SessionLocal
# from .core.config import settings
