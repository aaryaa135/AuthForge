import uuid

from tests.conftest import client


def test_blacklisted_token_cannot_access_me():
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
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

    access_token = login.json()["access_token"]
    refresh_token = login.json()["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "refresh_token": refresh_token,
        },
    )

    assert logout.status_code == 200

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 401
