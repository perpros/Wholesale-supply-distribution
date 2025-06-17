"""
Pytest Configuration and Fixtures.

This file defines shared fixtures for the test suite, including:
- Database setup and session management for tests.
- FastAPI TestClient instance.
- Fixtures for creating test users with different roles and authentication headers.
"""
import pytest
from typing import Generator, Any
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renamed to avoid conflict with fixture
from alembic.command import upgrade as alembic_upgrade
from alembic.config import Config as AlembicConfig

import sys
import os

# Add project root to sys.path to allow imports from 'backend'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from backend.app.main import app # Main FastAPI application
from backend.app.core.config import settings # Original settings for API_V1_STR etc.
from backend.app.db.session import get_db as original_get_db # Original get_db dependency
from backend.app.models import Base, User as UserModel, Role as RoleModel # SQLAlchemy Base and models

# --- Test Database Configuration ---
# Using in-memory SQLite for speed and simplicity in tests.
# Can be changed to a test PostgreSQL DB if needed.
TEST_DATABASE_URL = "sqlite:///./test.db"
# Example for PostgreSQL:
# TEST_DATABASE_URL = "postgresql://test_user:test_password@localhost:5432/test_product_need_db"
# Ensure the test DB user has permissions to create/drop DBs or use an existing one.

# Create a new SQLAlchemy engine for the test database
# connect_args is specific to SQLite for allowing multithreaded access (FastAPI runs in threads)
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)

# Create a sessionmaker for the test database
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Fixture to set up the test database at the beginning of the test session.
    - For SQLite: Creates all tables based on SQLAlchemy models.
    - For PostgreSQL (if configured): Applies Alembic migrations to 'head'.
    Handles teardown by dropping tables (SQLite) or potentially downgrading (PostgreSQL).
    """
    if "sqlite" in TEST_DATABASE_URL:
        Base.metadata.create_all(bind=engine) # Create tables
    else: # For PostgreSQL or other non-SQLite DBs, run Alembic migrations
        alembic_cfg_path = os.path.join(PROJECT_ROOT, "database/alembic.ini")
        alembic_script_location = os.path.join(PROJECT_ROOT, "database/migrations")

        if not os.path.exists(alembic_cfg_path):
            raise FileNotFoundError(f"Alembic config not found at {alembic_cfg_path}")
        if not os.path.exists(alembic_script_location):
             raise FileNotFoundError(f"Alembic migrations not found at {alembic_script_location}")

        alembic_cfg = AlembicConfig(alembic_cfg_path)
        alembic_cfg.set_main_option("script_location", alembic_script_location)
        # Override sqlalchemy.url from alembic.ini with the test database URL
        alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

        alembic_upgrade(alembic_cfg, "head") # Upgrade to the latest migration

    yield # Tests run here

    # Teardown after all tests in the session
    if "sqlite" in TEST_DATABASE_URL:
        Base.metadata.drop_all(bind=engine) # Drop all tables for SQLite
    # For PostgreSQL, teardown (like dropping DB or tables) might be handled externally
    # or by downgrading migrations, e.g., alembic_downgrade(alembic_cfg, "base")


@pytest.fixture(scope="function")
def db() -> Generator[SQLAlchemySession, None, None]:
    """
    Provides a database session for each test function.
    Uses a transactional approach: starts a transaction, yields the session,
    and rolls back the transaction after the test, ensuring test isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback() # Rollback any changes made during the test
        connection.close()


@pytest.fixture(scope="module")
def client(setup_test_database) -> Generator[TestClient, None, None]: # Ensure DB is set up
    """
    Provides a FastAPI TestClient instance.
    Overrides the application's `get_db` dependency to use the test database session.
    """
    def override_get_db_for_tests():
        """Dependency override for get_db to use the test database."""
        try:
            test_db = TestingSessionLocal()
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[original_get_db] = override_get_db_for_tests

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear() # Clean up overrides after tests in the module


# --- Utility and Authentication Fixtures ---

@pytest.fixture(scope="session") # Password can be session-scoped
def test_user_password() -> str:
    return "aSecureTestPassword123!"

def _create_role_if_not_exists(db: SQLAlchemySession, name: str, description: Optional[str] = None) -> RoleModel:
    role = db.query(RoleModel).filter(RoleModel.name == name).first()
    if not role:
        role = RoleModel(name=name, description=description or f"{name} role")
        db.add(role)
        db.commit()
        db.refresh(role)
    return role

@pytest.fixture(scope="function")
def test_user(db: SQLAlchemySession, test_user_password: str) -> UserModel:
    from backend.app.crud import user as crud_user
    from backend.app.schemas import UserCreate

    _create_role_if_not_exists(db, "End User", "Default role for end users.")
    # crud_user.create will assign "End User" role by default.

    user_in = UserCreate(
        email="testuser@example.com",
        password=test_user_password,
        full_name="Test User",
        is_active=True
    )
    user = crud_user.create(db, obj_in=user_in)
    # Ensure roles are loaded for assertions later if needed, crud.create should handle this.
    db.refresh(user, attribute_names=['roles'])
    return user

@pytest.fixture(scope="function")
def test_supplier_user(db: SQLAlchemySession, test_user_password: str) -> UserModel:
    from backend.app.crud import user as crud_user
    from backend.app.schemas import UserCreate

    _create_role_if_not_exists(db, "End User", "Default role for end users.")
    supplier_role = _create_role_if_not_exists(db, "Supplier", "Supplier role for submitting proposals.")

    user_in = UserCreate(email="supplier@example.com", password=test_user_password, full_name="Test Supplier")
    user = crud_user.create(db, obj_in=user_in) # Gets "End User" role by default

    # Remove "End User" role and add "Supplier" if user should only be supplier
    current_roles = {role.name for role in user.roles}
    if "End User" in current_roles:
        user.roles = [r for r in user.roles if r.name != "End User"]
    if supplier_role not in user.roles:
        user.roles.append(supplier_role)

    db.commit()
    db.refresh(user)
    db.refresh(user, attribute_names=['roles']) # Ensure roles are loaded
    return user

@pytest.fixture(scope="function")
def test_admin_user(db: SQLAlchemySession, test_user_password: str) -> UserModel:
    from backend.app.crud import user as crud_user
    from backend.app.schemas import UserCreate

    _create_role_if_not_exists(db, "End User", "Default role for end users.")
    admin_role = _create_role_if_not_exists(db, "Admin", "Administrator role with full access.")

    user_in = UserCreate(email="admin@example.com", password=test_user_password, full_name="Test Admin")
    user = crud_user.create(db, obj_in=user_in) # Gets "End User" role by default

    # Ensure user has Admin role and optionally remove End User if it's exclusive
    current_roles = {role.name for role in user.roles}
    if "End User" in current_roles: # Example: Admins might not also be "End Users"
         user.roles = [r for r in user.roles if r.name != "End User"]
    if admin_role not in user.roles:
        user.roles.append(admin_role)

    db.commit()
    db.refresh(user)
    db.refresh(user, attribute_names=['roles']) # Ensure roles are loaded
    return user

def _get_auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    if r.status_code != 200:
        pytest.fail(f"Failed to log in user {email}: {r.text} (Status: {r.status_code})")
    tokens = r.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def user_auth_headers(client: TestClient, test_user: UserModel, test_user_password: str) -> dict[str, str]:
    return _get_auth_headers(client, test_user.email, test_user_password)

@pytest.fixture(scope="function")
def supplier_auth_headers(client: TestClient, test_supplier_user: UserModel, test_user_password: str) -> dict[str, str]:
    return _get_auth_headers(client, test_supplier_user.email, test_user_password)

@pytest.fixture(scope="function")
def admin_auth_headers(client: TestClient, test_admin_user: UserModel, test_user_password: str) -> dict[str, str]:
    return _get_auth_headers(client, test_admin_user.email, test_user_password)
