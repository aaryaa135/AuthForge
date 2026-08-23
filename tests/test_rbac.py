import os
import uuid

from dotenv import load_dotenv

from tests.conftest import client
from tests.utils import create_test_admin

load_dotenv(".env.test")


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

    assert login.status_code == 200

    access_token = login.json()["access_token"]

    response = client.get(
        "/api/v1/users/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403


def test_admin_can_access_users():
    """
    Admin should access user list.
    """

    create_test_admin()

    login = client.post(
        "/api/v1/auth/login",
        data={
            "username": os.getenv("TEST_ADMIN_EMAIL"),
            "password": os.getenv("TEST_ADMIN_PASSWORD"),
        },
    )

    assert login.status_code == 200

    access_token = login.json()["access_token"]

    response = client.get(
        "/api/v1/users/",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200
