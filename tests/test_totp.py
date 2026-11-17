import uuid

import pyotp

from tests.conftest import client


def test_totp_login_verification_flow():
    """
    Test complete TOTP login verification flow.
    1. Register user
    2. Enable TOTP (creates unverified device, returns secret + QR + backup codes)
    3. Verify TOTP setup (marks device as verified)
    4. Login (triggers TWO_FACTOR_REQUIRED since 2FA is enabled)
    5. Call /2fa/login-verify with user_id and TOTP token
    6. Verify tokens are issued and user can access /me
    """

    # Step 1: Register user
    email = f"totp_{uuid.uuid4().hex[:8]}@example.com"
    username = f"totpuser_{uuid.uuid4().hex[:8]}"
    password = "Password@123"

    register_response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    assert register_response.status_code == 201

    # Step 2: Enable TOTP (creates unverified device)
    totp_enable = client.post("/api/v1/auth/2fa/enable")
    assert totp_enable.status_code == 200
    totp_data = totp_enable.json()
    assert "secret" in totp_data
    assert "qr_code" in totp_data
    assert "backup_codes" in totp_data
    totp_secret = totp_data["secret"]

    # Step 3: Verify TOTP setup (marks device as verified)
    client.post(
        "/api/v1/auth/2fa/verify-setup",
        json={"token": totp_data["secret"]},
    )
    # Verify device is now verified
    status_response = client.get("/api/v1/auth/2fa/status")
    assert status_response.status_code == 200
    assert status_response.json()["enabled"] is True

    # Step 4: Login (should require 2FA since device is verified)
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data.get("two_factor_required") is True
    user_id = login_data.get("user_id")
    assert user_id is not None

    # Step 5: Call /2fa/login-verify with user_id and TOTP token
    totp = pyotp.TOTP(totp_secret)
    totp_token = totp.now()

    verify_response = client.post(
        "/api/v1/auth/2fa/login-verify",
        data={"user_id": user_id, "token": totp_token},
    )
    assert verify_response.status_code == 200
    verify_data = verify_response.json()
    assert "access_token" in verify_data
    assert "refresh_token" in verify_data

    # Step 6: Verify the access token works on /me
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {verify_data['access_token']}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["is_verified"] is True
