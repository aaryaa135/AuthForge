import uuid

from tests.conftest import client


def test_logout():
    """
    Test logout.
    """

    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    username = f"user_{uuid.uuid4().hex[:8]}"
    password = "Password@123"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
        },
    )

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    refresh_token = login.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200
