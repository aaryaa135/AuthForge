import uuid

from tests.conftest import client


def test_change_password():
    """
    Test authenticated password change.
    """

    email = f"change_{uuid.uuid4().hex[:8]}@example.com"
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

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    access_token = login.json()["access_token"]

    response = client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": password,
            "new_password": "NewPassword@123",
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
