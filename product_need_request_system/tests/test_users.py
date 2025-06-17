import pytest
from httpx import AsyncClient
from fastapi import status
from app.schemas import UserRole # UserRole from app.schemas

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

async def test_create_user_success(client: AsyncClient):
    response = await client.post("/api/v1/users/", json={
        "name": "New Test User",
        "email": "newtestuser@example.com",
        "password": "strongpassword123",
        "role": UserRole.END_USER.value # Use .value for the string representation
    })
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newtestuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data # Ensure password is not returned
    assert data["name"] == "New Test User"
    assert data["role"] == UserRole.END_USER.value

async def test_create_user_duplicate_email_fails(client: AsyncClient, test_user_factory):
    # Create an initial user using the factory
    test_user_factory(email="duplicate@example.com", password="password1", role=UserRole.END_USER)

    # Attempt to create another user with the same email
    response = await client.post("/api/v1/users/", json={
        "name": "Another User",
        "email": "duplicate@example.com", # Duplicate email
        "password": "password2",
        "role": UserRole.SUPPLIER.value
    })
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Email already registered"

async def test_login_for_access_token_success(client: AsyncClient, test_user_factory):
    # Use the factory to create a user specifically for this test
    user_email = "login.success@example.com"
    user_password = "log_me_in"
    test_user_factory(email=user_email, password=user_password, role=UserRole.END_USER)

    response = await client.post("/api/v1/auth/token", data={
        "username": user_email,
        "password": user_password
    })
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

async def test_login_for_access_token_wrong_password_fails(client: AsyncClient, test_user_factory):
    user_email = "login.fail.pw@example.com"
    user_password = "correctpassword"
    test_user_factory(email=user_email, password=user_password, role=UserRole.END_USER)

    response = await client.post("/api/v1/auth/token", data={
        "username": user_email,
        "password": "wrongpassword" # Incorrect password
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["detail"] == "Incorrect email or password"

async def test_login_for_access_token_user_not_found_fails(client: AsyncClient):
    response = await client.post("/api/v1/auth/token", data={
        "username": "nonexistentuser@example.com",
        "password": "anypassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Or 404 if your auth logic distinguishes
    data = response.json()
    assert data["detail"] == "Incorrect email or password" # As per current auth logic

async def test_read_users_me_success(client: AsyncClient, end_user_auth_headers, test_user_factory):
    # The end_user_auth_headers fixture uses "enduser.test@example.com"
    # It's created by test_user_factory which is session-scoped for user creation,
    # but the headers fixture itself is function-scoped.
    response = await client.get("/api/v1/users/me", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "enduser.test@example.com" # Matches email used in fixture

async def test_read_users_me_no_auth_fails(client: AsyncClient):
    response = await client.get("/api/v1/users/me") # No auth headers
    assert response.status_code == status.HTTP_401_UNAUTHORIZED # Expecting 401

async def test_admin_can_read_all_users(client: AsyncClient, admin_auth_headers):
    # Fixture admin_auth_headers provides token for "admin.test@example.com"
    response = await client.get("/api/v1/users/", headers=admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Optionally, verify that users created by fixtures are in the list
    # emails_in_response = [user['email'] for user in data]
    # assert "admin.test@example.com" in emails_in_response

async def test_non_admin_cannot_read_all_users(client: AsyncClient, end_user_auth_headers):
    response = await client.get("/api/v1/users/", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_admin_can_read_specific_user(client: AsyncClient, admin_auth_headers, test_user_factory):
    # Create a user whose details admin will fetch
    target_user, _ = test_user_factory("target.user@example.com", "password", UserRole.SUPPLIER)

    response = await client.get(f"/api/v1/users/{target_user.id}", headers=admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "target.user@example.com"
    assert data["id"] == target_user.id

async def test_non_admin_cannot_read_specific_user(client: AsyncClient, end_user_auth_headers, test_user_factory):
    target_user, _ = test_user_factory("target.user.noaccess@example.com", "password", UserRole.SUPPLIER)

    response = await client.get(f"/api/v1/users/{target_user.id}", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
