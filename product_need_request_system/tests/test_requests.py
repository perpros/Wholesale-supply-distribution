import pytest
from httpx import AsyncClient, HTTPStatusError
from fastapi import status
from datetime import date, timedelta
from app.schemas import RequestStatus, UserRole
from app import crud, models

# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

# Helper function to create a request
async def create_request_as_user_helper(client: AsyncClient, user_auth_headers: dict,
                                  product_type: str = "Test Product", quantity: int = 10,
                                  days_offset_promised: int = 30, days_offset_expiration: int = 60,
                                  custom_payload: dict = None) -> dict:
    if custom_payload:
        payload = custom_payload
    else:
        payload = {
            "product_type": product_type,
            "quantity": quantity,
            "promised_delivery_date": (date.today() + timedelta(days=days_offset_promised)).isoformat(),
            "expiration_date": (date.today() + timedelta(days=days_offset_expiration)).isoformat()
        }
    response = await client.post("/api/v1/requests/", json=payload, headers=user_auth_headers)
    response.raise_for_status()
    return response.json()


# --- Test Create Request (from previous step, kept for completeness) ---
async def test_end_user_can_create_request_success(client: AsyncClient, end_user_auth_headers):
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="Laptop X1")
    assert created_request["product_type"] == "Laptop X1"
    assert created_request["quantity"] == 10
    assert created_request["status"] == RequestStatus.SUBMITTED.value

async def test_admin_can_create_request_success(client: AsyncClient, admin_auth_headers):
    created_request = await create_request_as_user_helper(client, admin_auth_headers, product_type="Admin Laptop")
    assert created_request["product_type"] == "Admin Laptop"
    assert created_request["status"] == RequestStatus.SUBMITTED.value

async def test_supplier_cannot_create_request(client: AsyncClient, supplier_auth_headers):
    with pytest.raises(HTTPStatusError) as exc_info:
        await create_request_as_user_helper(client, supplier_auth_headers, product_type="Supplier Laptop Attempt")
    assert exc_info.value.response.status_code == status.HTTP_403_FORBIDDEN


# --- Test Edit Requests ---
async def test_owner_can_edit_submitted_request(client: AsyncClient, end_user_auth_headers):
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="Editable Laptop")
    request_id = created_request["id"]

    update_payload = {"product_type": "Updated Laptop Model", "quantity": 5}
    response = await client.put(f"/api/v1/requests/{request_id}", json=update_payload, headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    updated_data = response.json()
    assert updated_data["product_type"] == "Updated Laptop Model"
    assert updated_data["quantity"] == 5
    assert updated_data["status"] == RequestStatus.SUBMITTED.value

async def test_owner_cannot_edit_approved_request(client: AsyncClient, end_user_auth_headers, admin_auth_headers, default_end_user):
    end_user_model, _ = default_end_user
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="To Be Approved Laptop")
    request_id = created_request["id"]

    await client.post(f"/api/v1/admin/requests/{request_id}/accept", headers=admin_auth_headers)
    response_approve = await client.post(f"/api/v1/admin/requests/{request_id}/approve", headers=admin_auth_headers)
    assert response_approve.status_code == status.HTTP_200_OK


    update_payload = {"product_type": "Attempted Edit on Approved"}
    response_edit = await client.put(f"/api/v1/requests/{request_id}", json=update_payload, headers=end_user_auth_headers)
    assert response_edit.status_code == status.HTTP_403_FORBIDDEN

async def test_other_end_user_cannot_edit_request(client: AsyncClient, end_user_auth_headers, test_user_factory):
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="Owner's Laptop")
    request_id = created_request["id"]

    _, other_user_token = test_user_factory("other.enduser@example.com", "password", UserRole.END_USER)
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    update_payload = {"product_type": "Malicious Edit Attempt"}
    response = await client.put(f"/api/v1/requests/{request_id}", json=update_payload, headers=other_user_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN

async def test_admin_can_edit_other_users_submitted_request(client: AsyncClient, end_user_auth_headers, admin_auth_headers):
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="User Laptop for Admin Edit")
    request_id = created_request["id"]

    update_payload = {"product_type": "Admin Corrected Laptop Model", "quantity": 7}
    response = await client.put(f"/api/v1/requests/{request_id}", json=update_payload, headers=admin_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    updated_data = response.json()
    assert updated_data["product_type"] == "Admin Corrected Laptop Model"
    assert updated_data["quantity"] == 7


# --- Test Cancel Requests ---
async def test_owner_can_cancel_submitted_request(client: AsyncClient, end_user_auth_headers):
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="To Be Cancelled Laptop")
    request_id = created_request["id"]

    response = await client.post(f"/api/v1/requests/{request_id}/cancel", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    cancelled_data = response.json()
    assert cancelled_data["status"] == RequestStatus.CANCELLED.value

async def test_owner_can_cancel_approved_request(client: AsyncClient, end_user_auth_headers, admin_auth_headers, default_end_user):
    end_user_model, _ = default_end_user
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="Approved then Cancelled Laptop")
    request_id = created_request["id"]

    await client.post(f"/api/v1/admin/requests/{request_id}/accept", headers=admin_auth_headers)
    await client.post(f"/api/v1/admin/requests/{request_id}/approve", headers=admin_auth_headers)

    response = await client.post(f"/api/v1/requests/{request_id}/cancel", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_200_OK
    cancelled_data = response.json()
    assert cancelled_data["status"] == RequestStatus.CANCELLED.value

async def test_cannot_cancel_closed_request(client: AsyncClient, end_user_auth_headers, default_admin, db_session, default_end_user):
    end_user_model, _ = default_end_user
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="To Be Closed Laptop Corrected")
    request_id = created_request["id"]

    db_req = db_session.query(models.Request).filter(models.Request.id == request_id).first()
    assert db_req is not None

    admin_model, _ = default_admin

    crud.update_request_status(db=db_session, db_request=db_req, new_status=schemas.RequestStatus.CLOSED, changed_by_user_id=admin_model.id)
    db_session.commit()

    response = await client.post(f"/api/v1/requests/{request_id}/cancel", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


# --- Test Resubmit Requests ---
async def test_owner_can_resubmit_rejected_request(client: AsyncClient, end_user_auth_headers, admin_auth_headers, default_end_user):
    end_user_model, _ = default_end_user
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="To Be Rejected Laptop")
    request_id = created_request["id"]

    response_reject = await client.post(f"/api/v1/admin/requests/{request_id}/reject", headers=admin_auth_headers)
    assert response_reject.status_code == status.HTTP_200_OK


    response_resubmit = await client.post(f"/api/v1/requests/{request_id}/resubmit", headers=end_user_auth_headers)
    assert response_resubmit.status_code == status.HTTP_200_OK
    resubmitted_data = response_resubmit.json()
    assert resubmitted_data["status"] == RequestStatus.RESUBMITTED.value

async def test_cannot_resubmit_approved_request(client: AsyncClient, end_user_auth_headers, admin_auth_headers, default_end_user):
    end_user_model, _ = default_end_user
    created_request = await create_request_as_user_helper(client, end_user_auth_headers, product_type="Approved, No Resubmit")
    request_id = created_request["id"]

    await client.post(f"/api/v1/admin/requests/{request_id}/accept", headers=admin_auth_headers)
    await client.post(f"/api/v1/admin/requests/{request_id}/approve", headers=admin_auth_headers)

    response = await client.post(f"/api/v1/requests/{request_id}/resubmit", headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Request can only be resubmitted if 'rejected' or 'cancelled'" in data["detail"]

# Validation tests from previous step (can be kept or moved if file gets too long)
async def test_create_request_missing_product_type_fails(client: AsyncClient, end_user_auth_headers):
    payload = { "quantity": 5, "promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(), "expiration_date": (date.today() + timedelta(days=60)).isoformat()}
    response = await client.post("/api/v1/requests/", json=payload, headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_request_quantity_less_than_one_fails(client: AsyncClient, end_user_auth_headers):
    payload = {"product_type": "Zero Q Prod", "quantity": 0, "promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(), "expiration_date": (date.today() + timedelta(days=60)).isoformat()}
    response = await client.post("/api/v1/requests/", json=payload, headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_request_promised_date_in_past_fails(client: AsyncClient, end_user_auth_headers):
    payload = {"product_type": "Past Promise", "quantity": 1, "promised_delivery_date": (date.today() - timedelta(days=1)).isoformat(), "expiration_date": (date.today() + timedelta(days=60)).isoformat()}
    response = await client.post("/api/v1/requests/", json=payload, headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_request_expiration_date_before_promised_fails(client: AsyncClient, end_user_auth_headers):
    payload = {"product_type": "Bad Dates", "quantity": 1, "promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(), "expiration_date": (date.today() + timedelta(days=15)).isoformat()}
    response = await client.post("/api/v1/requests/", json=payload, headers=end_user_auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_create_request_no_auth_fails(client: AsyncClient):
    payload = {"product_type": "No Auth Product","quantity": 1,"promised_delivery_date": (date.today() + timedelta(days=30)).isoformat(),"expiration_date": (date.today() + timedelta(days=60)).isoformat()}
    response = await client.post("/api/v1/requests/", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

async def test_read_my_requests_returns_own_requests(client: AsyncClient, test_user_factory, db_session):
    user_email = "myrequests2@example.com" # Unique email for this test
    my_user, my_token = test_user_factory(email=user_email, password="password", role=UserRole.END_USER)
    my_headers = {"Authorization": f"Bearer {my_token}"}

    from app.schemas import RequestCreate as SchemaRequestCreate
    request1_in = SchemaRequestCreate(product_type="My Product Alpha", quantity=1, promised_delivery_date=date.today()+timedelta(days=10), expiration_date=date.today()+timedelta(days=20))
    request2_in = SchemaRequestCreate(product_type="My Product Beta", quantity=2, promised_delivery_date=date.today()+timedelta(days=11), expiration_date=date.today()+timedelta(days=22))

    crud.create_request(db=db_session, request=request1_in, user_id=my_user.id)
    crud.create_request(db=db_session, request=request2_in, user_id=my_user.id)

    other_user, _ = test_user_factory(email="otheruser2@example.com", password="password", role=UserRole.END_USER)
    other_request_in = SchemaRequestCreate(product_type="Other User Product Gamma", quantity=3, promised_delivery_date=date.today()+timedelta(days=12), expiration_date=date.today()+timedelta(days=24))
    crud.create_request(db=db_session, request=other_request_in, user_id=other_user.id)

    db_session.commit()

    response = await client.get("/api/v1/requests/mine", headers=my_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert {item["product_type"] for item in data} == {"My Product Alpha", "My Product Beta"}
    for item in data:
        assert item["user_id"] == my_user.id
