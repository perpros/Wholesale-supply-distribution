from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings # Used for API_V1_STR
from app.schemas.product_need_request import ProductNeedRequestCreate # Not directly used but good for reference
from datetime import date, timedelta

# Base URL for the endpoint
API_V1_STR = settings.API_V1_STR
ENDPOINT_URL = f"{API_V1_STR}/product-need-request"

def test_create_product_need_request_success(client: TestClient, db_session: Session):
    tomorrow = date.today() + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)

    data = {
        "product_type": "Laptop X1",
        "product_count": 10,
        "promised_delivery_date": tomorrow.isoformat(),
        "expiration_date": day_after_tomorrow.isoformat(),
    }
    response = client.post(ENDPOINT_URL, json=data)

    assert response.status_code == 201, response.text
    content = response.json()
    assert content["message"] == "ProductNeedRequest successfully submitted"
    assert "id" in content
    assert isinstance(content["id"], int)

def test_create_product_need_request_invalid_product_count(client: TestClient, db_session: Session):
    tomorrow = date.today() + timedelta(days=1)
    day_after_tomorrow = tomorrow + timedelta(days=1)

    data = {
        "product_type": "Keyboard",
        "product_count": 0, # Invalid
        "promised_delivery_date": tomorrow.isoformat(),
        "expiration_date": day_after_tomorrow.isoformat(),
    }
    response = client.post(ENDPOINT_URL, json=data)
    assert response.status_code == 422, response.text # Pydantic validation error
    content = response.json()
    assert "detail" in content
    assert any(err["loc"] == ["body", "product_count"] and "must be greater than 0" in err["msg"] for err in content["detail"])

def test_create_product_need_request_promised_date_in_past(client: TestClient, db_session: Session):
    yesterday = date.today() - timedelta(days=1)
    tomorrow = date.today() + timedelta(days=1)

    data = {
        "product_type": "Mouse",
        "product_count": 5,
        "promised_delivery_date": yesterday.isoformat(), # Invalid
        "expiration_date": tomorrow.isoformat(),
    }
    response = client.post(ENDPOINT_URL, json=data)
    assert response.status_code == 422, response.text
    content = response.json()
    assert "detail" in content
    assert any(err["loc"] == ["body", "promised_delivery_date"] and "Promised delivery date must be in the future" in err["msg"] for err in content["detail"])

def test_create_product_need_request_expiration_date_before_promised(client: TestClient, db_session: Session):
    tomorrow = date.today() + timedelta(days=1)
    today = date.today()

    data = {
        "product_type": "Monitor",
        "product_count": 2,
        "promised_delivery_date": tomorrow.isoformat(),
        "expiration_date": today.isoformat(), # Invalid
    }
    response = client.post(ENDPOINT_URL, json=data)
    assert response.status_code == 422, response.text
    content = response.json()
    assert "detail" in content
    assert any(err["loc"] == ["body", "expiration_date"] and "Expiration date must be after promised delivery date" in err["msg"] for err in content["detail"])

def test_create_product_need_request_missing_field(client: TestClient, db_session: Session):
    tomorrow = date.today() + timedelta(days=1)
    data = {
        "product_type": "Webcam",
        # product_count is missing
        "promised_delivery_date": tomorrow.isoformat(),
        "expiration_date": (tomorrow + timedelta(days=1)).isoformat(),
    }
    response = client.post(ENDPOINT_URL, json=data)
    assert response.status_code == 422, response.text
    content = response.json()
    assert "detail" in content
    assert any(err["loc"] == ["body", "product_count"] and "field required" in err["msg"] for err in content["detail"])

def test_create_product_need_request_empty_product_type(client: TestClient, db_session: Session):
    tomorrow = date.today() + timedelta(days=1)
    data = {
        "product_type": "", # Invalid
        "product_count": 1,
        "promised_delivery_date": tomorrow.isoformat(),
        "expiration_date": (tomorrow + timedelta(days=1)).isoformat(),
    }
    response = client.post(ENDPOINT_URL, json=data)
    assert response.status_code == 422, response.text
    content = response.json()
    assert "detail" in content
    assert any(err["loc"] == ["body", "product_type"] and "ensure this value has at least 1 characters" in err["msg"] for err in content["detail"])
