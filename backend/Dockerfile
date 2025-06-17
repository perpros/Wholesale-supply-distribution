# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Ensure the locale is set to handle UTF-8 correctly (good practice)
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set work directory
WORKDIR /app

# Install system dependencies (if any, e.g., for psycopg2 if not using -binary, or build-essential for some packages)
# For psycopg2-binary, system dependencies are usually not needed, but if using psycopg2 (source), you would need:
# RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy only requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code from the backend directory
# This assumes the Docker build context is the 'backend' directory.
# If context is project root, it would be COPY ./backend /app
COPY . /app/

# Expose port 8000 (or whatever port Uvicorn will run on)
EXPOSE 8000

# Command to run the application
# Uvicorn will look for an 'app' instance in a module named 'main.py'
# in the current WORKDIR (/app).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
