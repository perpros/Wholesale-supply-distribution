import pytest
from typing import Generator, Any
from fastapi import FastAPI
from httpx import AsyncClient # Use AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession # Rename to avoid clash with pytest Session
from alembic.config import Config
from alembic import command
import os # For environment variables

# Assuming your app structure allows these imports
# Adjust paths if your app structure is different, e.g. from ..app import models
from app.database import Base, get_db
from app.main import app as main_app # Your FastAPI application instance
from app.models import User as UserModel # To avoid name clash with schema.User
from app.schemas import UserCreate, UserRole
from app.crud import create_user as crud_create_user
from app.security import create_access_token # get_password_hash is used by crud_create_user

# Use environment variable for test database URL, fallback to default if not set
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/product_db_test")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    print(f"Using database for testing: {TEST_DATABASE_URL}")
    alembic_cfg = Config("alembic.ini") # Assumes alembic.ini is in project root
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    print("Running Alembic upgrade head...")
    command.upgrade(alembic_cfg, "head")
    yield
    # For a truly clean slate between full test suite runs, you might downgrade to base.
    # print("Running Alembic downgrade base...")
    # command.downgrade(alembic_cfg, "base")
    # Or, more commonly, tests clean up their own data or use transactions.
    # If using drop_all/create_all per function, downgrade might be less critical here.

@pytest.fixture(scope="function")
def db_session() -> Generator[DBSession, Any, None]:
    # Before each test, clear and recreate tables.
    # This provides a clean slate for each test function.
    # `apply_migrations` ensures the schema is present for the session.
    # This drop_all/create_all is faster than running migrations per test,
    # but assumes Base reflects the migrated schema accurately.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback() # Rollback any uncommitted changes
        db.close()

@pytest.fixture(scope="function")
def test_app(db_session: DBSession) -> FastAPI:
    """
    Fixture to create a test instance of the FastAPI application,
    overriding the database dependency with the test session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            # db_session is closed by its own fixture's finally block
            pass

    main_app.dependency_overrides[get_db] = override_get_db
    return main_app

@pytest.fixture(scope="function")
async def client(test_app: FastAPI) -> AsyncClient:
    """
    Fixture to provide an HTTPX AsyncClient for making requests to the test app.
    """
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac

@pytest.fixture(scope="function")
def test_user_factory(db_session: DBSession):
    """
    Fixture factory to create users with specific roles and get their tokens.
    This allows creating multiple users with different roles within a single test if needed.
    """
    def _create_user_and_get_token(email: str, password: str, role: UserRole, name_prefix: str = "Test"):
        user_in_create = UserCreate(name=f"{name_prefix} {role.value}", email=email, password=password, role=role)
        # Ensure this user doesn't exist from a previous factory call in the same test session/db_session
        user_db = db_session.query(UserModel).filter(UserModel.email == email).first()
        if user_db: # If user somehow exists (e.g. from previous identical call in same test scope)
             pass # use existing user for token generation
        else:
            user_db = crud_create_user(db=db_session, user=user_in_create)

        token_data = {"sub": user_db.email}
        token = create_access_token(data=token_data)
        return user_db, token # Return the ORM model and token
    return _create_user_and_get_token

# Specific user role fixtures using the factory for pre-defined test users
# These ensure consistent users for roles across tests.
@pytest.fixture(scope="function")
def default_end_user(test_user_factory, db_session: DBSession) -> tuple[UserModel, str]:
    # Ensure this user is actually created/fetched via factory logic for consistency
    # The factory already handles checking if user exists by email.
    return test_user_factory(email="default_enduser@example.com", password="testpassword", role=UserRole.END_USER, name_prefix="DefaultEndUser")

@pytest.fixture(scope="function")
def default_supplier(test_user_factory, db_session: DBSession) -> tuple[UserModel, str]:
    return test_user_factory(email="default_supplier@example.com", password="testpassword", role=UserRole.SUPPLIER, name_prefix="DefaultSupplier")

@pytest.fixture(scope="function")
def default_admin(test_user_factory, db_session: DBSession) -> tuple[UserModel, str]:
    return test_user_factory(email="default_admin@example.com", password="testpassword", role=UserRole.ADMIN, name_prefix="DefaultAdmin")

@pytest.fixture(scope="function")
def end_user_auth_headers(default_end_user: tuple[UserModel, str]):
    _, token = default_end_user
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def supplier_auth_headers(default_supplier: tuple[UserModel, str]):
    _, token = default_supplier
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(default_admin: tuple[UserModel, str]):
    _, token = default_admin
    return {"Authorization": f"Bearer {token}"}


# Helper function (not a fixture) to create a request, can be defined in test files or a utility module
# async def create_request_as_user_helper(client: AsyncClient, user_auth_headers: dict,
#                                   product_type: str = "Test Product", quantity: int = 10,
#                                   days_offset_promised: int = 30, days_offset_expiration: int = 60) -> dict:
#     from datetime import date, timedelta # Keep imports local if it's a helper outside conftest
#     payload = {
#         "product_type": product_type,
#         "quantity": quantity,
#         "promised_delivery_date": (date.today() + timedelta(days=days_offset_promised)).isoformat(),
#         "expiration_date": (date.today() + timedelta(days=days_offset_expiration)).isoformat()
#     }
#     response = await client.post("/api/v1/requests/", json=payload, headers=user_auth_headers)
#     response.raise_for_status() # Raise an exception for bad status codes
#     return response.json()
