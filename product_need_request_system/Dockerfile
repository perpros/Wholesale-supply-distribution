# Base image: Use an official Python runtime.
# Using python:3.11-slim for a smaller image size.
FROM python:3.11-slim

# --- Environment Variables ---
# Prevents Python from writing .pyc files to disc (improves performance in Docker)
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to terminal without being buffered
ENV PYTHONUNBUFFERED 1
# Set the application environment (can be overridden by docker-compose)
# ENV APP_ENV production
# Set a default value for PYTHONPATH if your app structure needs it,
# though WORKDIR and copy structure should generally handle imports.
# ENV PYTHONPATH /app

# --- Working Directory ---
# Set the working directory in the container
WORKDIR /app

# --- Install System Dependencies (if needed) ---
# Example: For psycopg2, if not using the -binary version or if other libs are needed
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends gcc libpq-dev && \
#     rm -rf /var/lib/apt/lists/*

# --- Install Python Dependencies ---
# Copy only the requirements file first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code and Other Necessary Files ---
# Copy the backend application code into the /app/backend directory in the container
COPY ./backend /app/backend

# Copy Alembic configuration and migrations folder
# This allows running migrations from within the container (e.g., by backend service on startup or a separate migration job)
COPY ./database /app/database
COPY alembic.ini /app/alembic.ini
# Ensure alembic.ini paths (e.g., script_location) are relative or configurable
# if they need to work both locally and inside Docker.
# The default alembic.ini uses `script_location = database/migrations` which is fine with this structure.

# --- Expose Port ---
# Expose the port the FastAPI application will run on (default is 8000)
EXPOSE 8000

# --- Default Command ---
# The CMD will be specified in docker-compose.yml for different services (api, worker).
# Example for backend API service:
# CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
# Example for Celery worker:
# CMD ["celery", "-A", "backend.app.core.celery_app.celery_app", "worker", "-l", "info"]
# If this Dockerfile were intended for a single purpose, CMD would be set here.
# Since it's used by multiple services in docker-compose, CMD is omitted.
LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Dockerfile for the Product Need Request System backend and worker."
