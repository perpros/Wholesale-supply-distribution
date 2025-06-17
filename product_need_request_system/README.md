# Product Need Request System

This project is a system for managing product need requests, proposals, lifecycles, supplier interaction, and automated evaluations. It is built with a Python FastAPI backend, PostgreSQL database, Redis for caching/messaging, and Celery for background tasks.

## Features (Implemented)

*   **User Management:** Registration, login (OAuth2/JWT), role-based access control (End User, Supplier, Admin).
*   **Request Management:**
    *   End Users can create, view, update (in specific states), cancel, and resubmit their requests.
    *   Admins can approve, reject, and cancel requests.
    *   Automatic status logging for audit trails.
*   **Proposal Management:**
    *   Suppliers can submit proposals for approved requests.
    *   Proposals are subject to validation rules (one per supplier per request, request status/expiration).
    *   Role-based visibility of proposals.
*   **Background Tasks (Celery + Redis):**
    *   Automatic expiration of requests past their `expiration_date`.
    *   Automatic closure of expired requests (as `CLOSED_FULFILLED` or `CLOSED_UNFULFILLED`) based on whether the need was met by proposals.
*   **Database:** PostgreSQL with schema managed by Alembic migrations.
*   **API:** RESTful API built with FastAPI, with automatic OpenAPI documentation.
*   **Testing:** Pytest setup with unit and integration tests for key functionalities.
*   **Dockerization:** Fully containerized setup using Docker and Docker Compose for development and deployment.

## Project Structure

```
product_need_request_system/
├── alembic.ini             # Alembic configuration
├── Dockerfile              # Main Dockerfile for Python application
├── docker-compose.yml      # Docker Compose for orchestrating services
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (local, gitignored)
├── .dockerignore           # Docker ignore file
├── .gitignore              # Git ignore file
├── backend/                # FastAPI application source code
│   ├── app/
│   │   ├── api/            # API endpoints (routers, dependencies)
│   │   ├── core/           # Core logic (config, security, celery app)
│   │   ├── crud/           # CRUD operations for database models
│   │   ├── db/             # Database session management
│   │   ├── models/         # SQLAlchemy ORM models and enums
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic services
│   │   └── tasks/          # Celery background tasks
│   └── main.py           # FastAPI application entrypoint
├── database/               # Database related files
│   └── migrations/         # Alembic migration scripts
├── tests/                  # Pytest tests
└── README.md               # This file
```

## Prerequisites

*   Docker Desktop (or Docker Engine + Docker Compose)
*   A `.env` file at the project root (see instructions below for creation)

## Getting Started (Local Development with Docker)

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd product_need_request_system
    ```

2.  **Create Environment File:**
    Create a new file named `.env` at the project root (`product_need_request_system/.env`).
    Populate it with the following minimal content, replacing placeholder values:
    ```env
    POSTGRES_USER=your_pg_user
    POSTGRES_PASSWORD=your_pg_password
    POSTGRES_DB=product_need_dev_db

    # Generate a strong secret key using: openssl rand -hex 32
    # Example: SECRET_KEY=d1a8f7c3e2b1a0f9d8c7b6a5e4d3c2b1a0f9e8d7c6b5a4f3e2d1c0b9a8f7e6d5
    SECRET_KEY=a_very_strong_random_secret_key_32_chars_long
    ```
    Replace `your_pg_user`, `your_pg_password`, and the `SECRET_KEY` with your own secure values. The `SECRET_KEY` should be unpredictable and ideally 32 hexadecimal characters long (or have equivalent entropy).

3.  **Build and Run Docker Containers:**
    ```bash
    docker-compose up --build -d
    ```
    This command will:
    *   Build the Docker image for the Python application (FastAPI backend and Celery worker).
    *   Pull PostgreSQL and Redis images if not present locally.
    *   Start all services (database, redis, backend, worker) in detached mode (`-d`).
    The backend API will typically be available at `http://localhost:8000`.

4.  **Apply Database Migrations:**
    After the `db` service is healthy (check with `docker-compose ps`), run Alembic migrations. Execute this command in your terminal:
    ```bash
    docker-compose exec backend alembic upgrade head
    ```
    *(Note: For a more robust setup, an entrypoint script in the backend Docker image could automatically check and apply migrations on startup. This current setup requires manual migration execution after initial startup.)*

## Running Tests

Tests are run using Pytest. The test environment is configured in `tests/conftest.py` and typically uses an in-memory SQLite database for speed or a separate test PostgreSQL instance if configured.

1.  **Ensure backend container is running (it includes the test environment):**
    If you haven't started all services with `docker-compose up -d`, you might need to start the backend service specifically if tests rely on other services (though most unit/integration tests with a test DB might not).
    ```bash
    # Not usually needed if 'docker-compose up -d' was run and backend is up.
    # docker-compose up -d backend
    ```
2.  **Execute tests inside the `backend` container:**
    ```bash
    docker-compose exec backend pytest tests/
    ```
    This command runs all tests located in the `tests/` directory within the context of the `backend` service container.

## API Documentation

Once the backend service is running, interactive API documentation (Swagger UI) is available at:
`http://localhost:8000/docs`

The OpenAPI schema is available at:
`http://localhost:8000/openapi.json`

## Celery Worker and Beat

The `worker` service defined in `docker-compose.yml` runs a Celery worker process. The command `celery -A backend.app.core.celery_app.celery_app worker -l info -B` also includes the `-B` flag, which embeds the Celery Beat scheduler within the worker. This scheduler will periodically trigger the defined tasks (e.g., `auto_expire_requests_task`, `auto_close_requests_task`) based on their configured schedules (if any were set in `celery_app.py` or via other configuration).

For monitoring Celery tasks (optional, not included in current `docker-compose.yml`):
You can add a Flower service to `docker-compose.yml` for a web-based Celery monitoring tool.

## Code Structure Overview

*   **`backend/app/main.py`**: Entry point for the FastAPI application. Initializes the app and includes routers.
*   **`backend/app/core/`**: Core application logic:
    *   `config.py`: Pydantic settings management (environment variables, .env file).
    *   `security.py`: Password hashing, JWT creation, and token decoding utilities.
    *   `celery_app.py`: Celery application instance initialization and configuration.
*   **`backend/app/models/`**: SQLAlchemy ORM models defining database table structures and relationships. Includes `enums.py` for shared enumerations.
*   **`backend/app/schemas/`**: Pydantic schemas for data validation, serialization (API request/response shapes), and type hinting.
*   **`backend/app/crud/`**: CRUD (Create, Read, Update, Delete) operations. Provides a reusable `CRUDBase` and specific CRUD classes for each model (e.g., `crud_user`, `crud_request`).
*   **`backend/app/api/`**: API endpoint definitions:
    *   `deps.py`: FastAPI dependencies for common tasks like getting DB sessions, current user, and role checking.
    *   `v1/api.py`: Main router for API version 1.
    *   `v1/endpoints/`: Modules for specific resource endpoints (e.g., `login.py`, `users.py`, `requests.py`, `proposals.py`).
*   **`backend/app/services/`**: Business logic services that may orchestrate multiple CRUD operations or interact with external services (e.g., `request_service.py`).
*   **`backend/app/tasks/`**: Celery background task definitions (e.g., `request_tasks.py` for request lifecycle management).
*   **`database/migrations/`**: Alembic database migration scripts. Version files are stored in `versions/`. `env.py` configures Alembic execution.
*   **`tests/`**: Pytest tests, including `conftest.py` for fixtures and subdirectories for API or unit tests.

## Contributing

(This section can be expanded if this were an open project with multiple contributors.)

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/YourAmazingFeature`).
3.  Make your changes.
4.  Write tests for your changes.
5.  Ensure all tests pass (`docker-compose exec backend pytest tests/`).
6.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
7.  Push to the branch (`git push origin feature/YourAmazingFeature`).
8.  Open a Pull Request for review.

---

*This README provides a starting point. Feel free to expand sections or add new ones (e.g., Deployment, Troubleshooting, Detailed Configuration) as the project evolves.*
