# Backend for Wholesale Supply Distribution

This directory contains the FastAPI backend application.

## Database Migrations (Alembic)

Database migrations are managed using Alembic. The configuration for Alembic is in `alembic.ini` and the environment setup (including database URL sourcing) is in `alembic/env.py`.

**Key Points**:
-   The database URL for Alembic is sourced from the same application settings (`backend.app.core.config.settings.DATABASE_URL`) that the main application uses. This ensures consistency. Ensure your environment variables (especially `DATABASE_URL`) are correctly set up when running migration commands.
-   Migration scripts are located in `alembic/versions/`.

**Common Commands**:

1.  **Generate a new migration revision**:
    After making changes to your SQLAlchemy models in `backend/app/models/`, you need to generate a new migration script. Run this command from the `backend/` directory:
    ```bash
    alembic revision -m "short_description_of_changes"
    ```
    This will create a new file in `alembic/versions/`. Review this file and adjust as necessary, especially if autogenerate doesn't capture all changes perfectly (e.g., for complex constraints or custom types).

2.  **Apply migrations (upgrade to the latest revision)**:
    To apply all pending migrations to your database, run this command from the `backend/` directory:
    ```bash
    alembic upgrade head
    ```
    This will bring the database schema to the latest version.

3.  **Downgrade migrations (optional)**:
    You can downgrade to a specific version or by a number of steps. For example, to revert one migration:
    ```bash
    alembic downgrade -1
    ```
    To downgrade to a specific revision ID:
    ```bash
    alembic downgrade <revision_id>
    ```

4.  **Check current database revision**:
    ```bash
    alembic current
    ```

5.  **View migration history**:
    ```bash
    alembic history
    ```

## Initial Data Seeding

Strategies for seeding initial data (e.g., default roles, admin user) can be implemented using Alembic data migrations (by manipulating tables directly in a revision's `upgrade` function) or by creating dedicated Python scripts that use the CRUD utilities and SQLAlchemy session. This will be addressed as a future enhancement.

---

*Further details about running the application, dependencies, etc., should be added here.*
