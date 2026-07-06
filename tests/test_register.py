import uuid

from tests.conftest import client


def test_register_user():
    """
    Test successful user registration.
    """

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "password": "Password@123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"].endswith("@example.com")
    assert "id" in data
    assert data["is_active"] is True
