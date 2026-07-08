import uuid

from tests.conftest import client


def test_login_rate_limit():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"

    password = "Password@123"

    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": email,
            "password": password,
        },
    )

    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            data={
                "username": email,
                "password": "WrongPassword",
            },
        )

    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 429
