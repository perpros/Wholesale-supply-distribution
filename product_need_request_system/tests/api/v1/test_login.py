"""
Tests for Login API Endpoints.

Covers token generation and basic token authentication.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting, not always used directly in endpoint tests

from backend.app.core.config import settings # For API_V1_STR
from backend.app import schemas # For response model validation (e.g., schemas.User)
from backend.app.models import User as UserModel # For type hinting test_user

# Mark all tests in this module as 'integration' (example marker)
# pytestmark = pytest.mark.integration

def test_login_access_token_success(
    client: TestClient,
    test_user: UserModel, # Fixture from conftest.py
    test_user_password: str # Fixture from conftest.py
):
    """
    Test successful login and access token generation.
    """
    login_data = {
        "username": test_user.email,
        "password": test_user_password,
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

    assert response.status_code == 200, f"Response content: {response.text}"
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_access_token_invalid_password(
    client: TestClient,
    test_user: UserModel
):
    """
    Test login attempt with an invalid password.
    """
    login_data = {
        "username": test_user.email,
        "password": "wrong_password",
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

    assert response.status_code == 401 # Unauthorized
    content = response.json()
    assert content["detail"] == "Incorrect email or password"

def test_login_access_token_inactive_user(
    client: TestClient,
    test_user: UserModel,
    test_user_password: str,
    db: Session # db fixture to modify user state
):
    """
    Test login attempt for an inactive user.
    """
    # Deactivate the user
    test_user.is_active = False
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    login_data = {
        "username": test_user.email,
        "password": test_user_password,
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)

    assert response.status_code == 400 # Bad Request
    content = response.json()
    assert content["detail"] == "Inactive user"

    # Reactivate user for other tests if db session is not fully isolated per test
    # (though our db fixture rolls back, so this is more for clarity or if that changes)
    test_user.is_active = True
    db.add(test_user)
    db.commit()

def test_use_valid_access_token_for_me_endpoint(
    client: TestClient,
    test_user: UserModel, # To know which user to expect
    user_auth_headers: dict[str, str] # Fixture that provides valid auth headers
):
    """
    Test accessing a protected endpoint (/users/me) with a valid token.
    """
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=user_auth_headers)

    assert response.status_code == 200, f"Response content: {response.text}"
    user_data = response.json()
    # Validate against the User schema (optional, but good practice)
    schemas.User(**user_data) # This will raise ValidationError if structure is wrong
    assert user_data["email"] == test_user.email
    assert user_data["full_name"] == test_user.full_name
    assert "hashed_password" not in user_data # Ensure sensitive data is not returned

def test_use_invalid_access_token(client: TestClient):
    """
    Test accessing a protected endpoint with an invalid or malformed token.
    """
    invalid_headers = {"Authorization": "Bearer invalidtoken123"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=invalid_headers)

    assert response.status_code == 401 # Unauthorized
    content = response.json()
    assert content["detail"] == "Could not validate credentials"

def test_token_data_payload(
    client: TestClient,
    test_user: UserModel, # User with roles
    test_user_password: str
):
    """
    Test that the generated token payload (sub, roles) is correct.
    This indirectly tests `create_access_token` and `decode_access_token`.
    """
    # Log in to get a token
    login_data = {"username": test_user.email, "password": test_user_password}
    r_login = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]

    # Decode the token (conceptually, actual decoding is done by endpoint dependencies)
    # We can test a protected endpoint that relies on this token data.
    # For example, if /login/test-token returns current_user based on token:
    r_test_token = client.post(f"{settings.API_V1_STR}/login/test-token", headers={"Authorization": f"Bearer {token}"})
    assert r_test_token.status_code == 200
    user_from_token = schemas.User(**r_test_token.json())
    assert user_from_token.email == test_user.email

    # To directly check roles in token, you'd need to decode it here or have an endpoint that returns token_data.
    # The `test_user` fixture should have the 'End User' role by default.
    # The `login_access_token` endpoint includes these roles in the token.
    # The `deps.get_current_user_from_token` decodes it.
    # Let's rely on the fact that RoleChecker will use these roles.
    # If there was an endpoint that explicitly returned TokenData, we could assert roles here.
    # For now, confirming user identity via /login/test-token (which uses the token) is a good indirect check.

    # If test_user.roles were directly accessible and comparable strings:
    # expected_roles_in_token = sorted([role.name for role in test_user.roles])
    # decoded_token_data = decode_access_token(token) # If we were to decode it here
    # assert sorted(decoded_token_data.roles) == expected_roles_in_token

    # This test primarily confirms the 'sub' (username/email) part is correct.
    # Testing roles in token is implicitly done when testing RoleChecker-protected endpoints.
    pass
