"""
Test Utility Functions.

This module can contain helper functions for tests, such as:
- Generating random data (strings, numbers, emails).
- Common assertion helpers.
- Functions to create specific test objects if not covered by fixtures.
"""
import random
import string
from typing import Dict

# Example utility function
def random_lower_string(length: int = 8) -> str:
    """Generates a random lowercase string of a given length."""
    return "".join(random.choices(string.ascii_lowercase, k=length))

def random_email() -> str:
    """Generates a random email address."""
    domain = "".join(random.choices(string.ascii_lowercase, k=5))
    return f"{random_lower_string()}@{domain}.com"

# You might add more complex data generators here, e.g., for creating
# valid Pydantic schema payloads with random (but valid) data.

# Example: Generate request data
def generate_random_request_data(days_offset_promised: int = 10, days_offset_expiration: int = 20) -> Dict[str, Any]:
    from datetime import date, timedelta
    from app.models.enums import ProductTypeEnum # Assuming this path is correct

    return {
        "product_type": random.choice(list(ProductTypeEnum)).value,
        "quantity": random.randint(1, 100),
        "promised_delivery_date": (date.today() + timedelta(days=days_offset_promised)).isoformat(),
        "expiration_date": (date.today() + timedelta(days=days_offset_expiration)).isoformat(),
    }

# Add other utilities as your test suite grows.
# For example, a function to get a specific user's token if you test many users
# without creating a fixture for each one.
from fastapi.testclient import TestClient
from app.core.config import settings # For API_V1_STR

def get_user_token_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    """Helper to log in and get auth headers for any user."""
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    if r.status_code != 200:
        # Consider raising an error or returning None/empty dict based on how you want tests to fail
        raise Exception(f"Failed to log in user {email} for token generation: {r.text}")
    tokens = r.json()
    access_token = tokens["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
