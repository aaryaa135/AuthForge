import uuid

from tests.conftest import client


def test_forgot_password():
    """
    Test forgot password endpoint.
    """

    email = f"forgot_{uuid.uuid4().hex[:8]}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "Password@123"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    assert register.status_code == 201

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": email,
        },
    )

    assert response.status_code == 200


def test_forgot_password_unknown_email():
    """
    Unknown email should not crash the API.
    """

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={
            "email": "unknown@example.com",
        },
    )

    # Use the status code your implementation returns.
    # If you've intentionally made it always return 200 to avoid email
    # enumeration, keep 200. Otherwise change this to match your API.
    assert response.status_code == 200
