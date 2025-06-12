import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app # Main FastAPI app
from app.db.session import get_db # get_db dependency
from app.db.base_class import Base # Base for tables
from app.core.config import settings # To override settings (though not directly used here for URL)
from app.core.security import User, get_current_active_user as app_get_current_active_user # Import the actual dependency

# Use an in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in the test database
# This needs to happen after all models are imported, typically via their modules
# For ProductNeedRequest, it's in app.models.product_need_request
# Let's ensure that model is loaded before Base.metadata.create_all
from app.models.product_need_request import ProductNeedRequest

Base.metadata.create_all(bind=engine) # Now ProductNeedRequest table will be created

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    # Use the connection for the session in this fixture
    session = TestingSessionLocal(bind=connection)
    yield session
    # Close the session provided by this fixture
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Get a TestClient instance that uses the test_db session."""

    # This override provides the db_session fixture's session directly to the endpoint
    def override_get_db():
        yield db_session

    def mock_get_current_active_user(): # Renamed for clarity
        return User(username="testuser", email="test@example.com", active=True)

    app.dependency_overrides[get_db] = override_get_db
    # Use the imported dependency function as the key
    app.dependency_overrides[app_get_current_active_user] = mock_get_current_active_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear() # Clear overrides after test
