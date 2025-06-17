import pytest
from httpx import AsyncClient, HTTPStatusError
from fastapi import status
from datetime import date, timedelta # Not strictly needed for these initial proposal tests, but good for future.
from app.schemas import UserRole, RequestStatus # For setting up test data

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# Helper to setup an approved request (can be moved to conftest or a shared util if used by many test files)
async def create_approved_request(client: AsyncClient, end_user_headers: dict, admin_headers: dict, product_type: str = "Default Approved Product") -> int:
    """
    Creates a request as an end user, then accepts and approves it as an admin.
    Returns the ID of the approved request.
    """
    # 1. EndUser creates a request
    request_payload = {
        "product_type": product_type,
        "quantity": 10,
        "promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "expiration_date": (date.today() + timedelta(days=60)).isoformat()
    }
    response_create = await client.post("/api/v1/requests/", json=request_payload, headers=end_user_headers)
    response_create.raise_for_status()
    request_id = response_create.json()["id"]

    # 2. Admin accepts the request
    response_accept = await client.post(f"/api/v1/admin/requests/{request_id}/accept", headers=admin_headers)
    response_accept.raise_for_status()

    # 3. Admin approves the request
    response_approve = await client.post(f"/api/v1/admin/requests/{request_id}/approve", headers=admin_headers)
    response_approve.raise_for_status()

    return request_id

# --- Test Proposal Submission ---
async def test_supplier_can_submit_proposal_to_approved_request(
    client: AsyncClient, supplier_auth_headers, end_user_auth_headers, admin_auth_headers
):
    approved_request_id = await create_approved_request(client, end_user_auth_headers, admin_auth_headers, "Product For Proposal")

    proposal_payload = {"quantity": 5} # request_id is in path, not payload for this endpoint design
    response = await client.post(f"/api/v1/requests/{approved_request_id}/proposals/", json=proposal_payload, headers=supplier_auth_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["quantity"] == proposal_payload["quantity"]
    assert data["request_id"] == approved_request_id
    # supplier_id should match the current supplier's ID. Requires fetching supplier user or more complex check.
    # For now, trust the backend sets it from the token.
    assert "id" in data
    assert "supplier_id" in data # Ensure supplier_id is part of the response

async def test_submit_proposal_to_submitted_request_fails(
    client: AsyncClient, supplier_auth_headers, end_user_auth_headers
):
    # 1. EndUser creates a request (it will be in 'submitted' state)
    request_payload = {
        "product_type": "Still Submitted Product",
        "quantity": 10,
        "promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(),
        "expiration_date": (date.today() + timedelta(days=60)).isoformat()
    }
    response_create = await client.post("/api/v1/requests/", json=request_payload, headers=end_user_auth_headers)
    response_create.raise_for_status()
    submitted_request_id = response_create.json()["id"]

    # 2. Supplier attempts to submit proposal
    proposal_payload = {"quantity": 5}
    response = await client.post(f"/api/v1/requests/{submitted_request_id}/proposals/", json=proposal_payload, headers=supplier_auth_headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Proposals can only be submitted for 'approved' requests" in data["detail"]

async def test_end_user_cannot_submit_proposal(
    client: AsyncClient, end_user_auth_headers, admin_auth_headers # Need admin to approve a request
):
    approved_request_id = await create_approved_request(client, end_user_auth_headers, admin_auth_headers, "Product For EndUser Fail")

    proposal_payload = {"quantity": 3}
    response = await client.post(f"/api/v1/requests/{approved_request_id}/proposals/", json=proposal_payload, headers=end_user_auth_headers) # Using end_user headers

    assert response.status_code == status.HTTP_403_FORBIDDEN # Because endpoint requires_supplier

async def test_submit_proposal_quantity_less_than_one_fails(
    client: AsyncClient, supplier_auth_headers, end_user_auth_headers, admin_auth_headers
):
    approved_request_id = await create_approved_request(client, end_user_auth_headers, admin_auth_headers, "Product For Zero Quant Proposal")

    proposal_payload = {"quantity": 0} # Invalid quantity
    response = await client.post(f"/api/v1/requests/{approved_request_id}/proposals/", json=proposal_payload, headers=supplier_auth_headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY # Pydantic validation

async def test_supplier_cannot_submit_duplicate_proposal_to_same_request(
    client: AsyncClient, supplier_auth_headers, end_user_auth_headers, admin_auth_headers
):
    approved_request_id = await create_approved_request(client, end_user_auth_headers, admin_auth_headers, "Product For Duplicate Proposal")

    # First proposal submission
    proposal_payload1 = {"quantity": 7}
    response1 = await client.post(f"/api/v1/requests/{approved_request_id}/proposals/", json=proposal_payload1, headers=supplier_auth_headers)
    assert response1.status_code == status.HTTP_201_CREATED

    # Attempt to submit a second proposal by the same supplier
    proposal_payload2 = {"quantity": 3}
    response2 = await client.post(f"/api/v1/requests/{approved_request_id}/proposals/", json=proposal_payload2, headers=supplier_auth_headers)

    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    data = response2.json()
    assert "Supplier already submitted a proposal for this request" in data["detail"]

# More tests to come:
# - Listing proposals for a request (by end user, by supplier, by admin)
# - Getting a specific proposal (by owner, by request owner, by admin)
# - Updating a proposal (by owner, when request is approved, when request is not approved)
# - Deleting a proposal (by owner, by admin)
