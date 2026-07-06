import uuid
from tests.conftest import client

import os
from dotenv import load_dotenv

load_dotenv(".env.test")

ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD")


def test_user_cannot_access_users_endpoint():
    """
    Normal users should not access admin endpoints.
    """

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

    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 403


def test_admin_can_access_users():
    """
    Admin should access user list.
    """

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        },
    )

    assert login.status_code == 200

    access_token = login.json()["access_token"]

    response = client.get(
        "/users/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
