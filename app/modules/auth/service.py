import base64
import hashlib
import io
from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe
from uuid import uuid4

import pyotp
import qrcode

from app.cache.service import CacheService
from app.core.config import settings
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.logger import logger
from app.core.security import hash_password, verify_password
from app.modules.audit.service import AuditService
from app.modules.auth.models import (
    ApiKey,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    TotpDevice,
)
from app.modules.auth.repository import (
    ApiKeyRepository,
    EmailVerificationRepository,
    PasswordResetRepository,
    RefreshTokenRepository,
    TotpDeviceRepository,
    UserSessionRepository,
)
from app.modules.auth.schemas import (
    ApiKeyCreateResponse,
    ApiKeyResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    TotpEnableResponse,
    TotpStatusResponse,
    TotpVerifyResponse,
)
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from app.providers.base import EmailProvider


class AuthService:
    """
    Handles authentication business logic.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_reset_repository: PasswordResetRepository,
        email_verification_repository: EmailVerificationRepository,
        totp_device_repository: TotpDeviceRepository,
        api_key_repository: ApiKeyRepository,
        user_session_repository: UserSessionRepository,
        email_provider: EmailProvider,
        audit_service: AuditService,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_reset_repository = password_reset_repository
        self.email_verification_repository = email_verification_repository
        self.totp_device_repository = totp_device_repository
        self.api_key_repository = api_key_repository
        self.user_session_repository = user_session_repository
        self.email_provider = email_provider
        self.cache = CacheService()
        self.audit_service = audit_service

    def register_user(
        self,
        user_data: UserCreate,
        ip_address: str | None = None,
    ) -> User:
        """
        Register a new user.

        Returns the created user. If email or username already exists, returns
        the existing user without leaking which field is taken (anti-enumeration).
        """

        # Check email - generic handling to prevent enumeration
        existing_email = self.user_repository.get_by_email(user_data.email)
        existing_username = self.user_repository.get_by_username(user_data.username)

        if existing_email is not None or existing_username is not None:
            # Return a generic response; do not reveal which field is taken.
            user = existing_email or existing_username
            logger.warning(
                "Registration attempt for existing email/username: %s",
                user_data.email,
            )
            return user

        # Default role
        default_role = self.role_repository.get_by_name("User")

        if default_role is None:
            raise ValueError("Default role not found.")

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            role_id=default_role.id,
            is_active=True,
            is_verified=False,
        )

        created_user = self.user_repository.create(user)

        self.audit_service.log(
            action="REGISTER",
            success=True,
            user_id=created_user.id,
            ip_address=ip_address,
        )

        verification_token = token_urlsafe(32)

        verification = EmailVerificationToken(
            token=verification_token,
            user_id=created_user.id,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

        self.email_verification_repository.create(verification)

        logger.info(
            "Email verification token created for %s",
            created_user.email,
        )

        verification_link = (
            f"{settings.frontend_url}/api/v1/auth/verify-email?token={verification_token}"
        )

        self.email_provider.send_verification_email(
            created_user.email,
            verification_link,
        )

        logger.info(
            "User registered: %s",
            created_user.email,
        )

        return created_user

    def _issue_tokens(
        self,
        user: User,
    ) -> TokenResponse:
        """
        Generate and persist new access and refresh tokens.
        """

        access_token = create_access_token(
            subject=str(user.id),
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        family_id = uuid4()

        refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            family_id=family_id,
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
        )

        self.refresh_token_repository.create(refresh)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def login_user(
        self,
        identifier: str,
        password: str,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """
        Authenticate user using email or username.
        Includes progressive account lockout after repeated failures.
        """

        lock_key = f"login_lock:{identifier}"
        fail_key = f"login_failures:{identifier}"
        max_failures = 5
        lockout_seconds = 900  # 15 minutes

        # Check if account is currently locked
        if self.cache.exists(lock_key):
            logger.warning(
                "Login attempt on locked account: %s",
                identifier,
            )
            raise ValueError(
                "Account temporarily locked due to failed login attempts. Try again later."
            )

        if "@" in identifier:
            user = self.user_repository.get_by_email(identifier)
        else:
            user = self.user_repository.get_by_username(identifier)

        if user is None:
            logger.warning(
                "Invalid login attempt: %s",
                identifier,
            )
            self._record_failed_attempt(fail_key, max_failures, lockout_seconds)
            raise ValueError("Invalid credentials.")

        if not user.is_active:
            logger.warning(
                "Login attempt on inactive account: %s",
                identifier,
            )
            self._record_failed_attempt(fail_key, max_failures, lockout_seconds)
            raise ValueError("Invalid credentials.")

        if not verify_password(
            password,
            user.hashed_password,
        ):
            logger.warning(
                "Invalid login attempt: %s",
                identifier,
            )
            self._record_failed_attempt(fail_key, max_failures, lockout_seconds)
            raise ValueError("Invalid credentials.")

        if settings.require_email_verification and not user.is_verified:
            logger.warning(
                "Login attempt on unverified account: %s",
                identifier,
            )
            self._record_failed_attempt(fail_key, max_failures, lockout_seconds)
            raise ValueError("Invalid credentials.")

        logger.info(
            "User logged in: %s",
            user.email,
        )

        self.audit_service.log(
            action="LOGIN",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        # If user has 2FA enabled, require second step before issuing tokens
        device = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)
        if device is not None and device.is_verified:
            # Store pending 2FA state in Redis (5 minute TTL)
            pending_key = f"2fa_pending:{user.id}"
            self.cache.set(pending_key, "1", ttl=300)
            raise ValueError("TWO_FACTOR_REQUIRED")

        return self._issue_tokens(user)

    def refresh_tokens(
        self,
        request: RefreshTokenRequest,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """
        Rotate refresh token and issue a new access token.
        """

        # Decode JWT
        payload = decode_token(request.refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token.")

        # Ensure it's actually a refresh token
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        # Find token in DB
        stored_token = self.refresh_token_repository.get_by_token(request.refresh_token)

        if stored_token is None:
            raise ValueError("Refresh token not found.")

        # Check revocation - reuse detection: revoke entire family
        if stored_token.is_revoked:
            self.refresh_token_repository.revoke_family(stored_token.family_id)
            logger.warning(
                "Refresh token reuse detected for family %s",
                stored_token.family_id,
            )
            self.audit_service.log(
                action="TOKEN_REUSE_DETECTED",
                success=False,
                user_id=stored_token.user_id,
                ip_address=ip_address,
            )
            raise ValueError("Refresh token revoked. Token family revoked due to reuse.")

        # Check user is still active
        user = stored_token.user
        if not user.is_active:
            raise ValueError("User account is inactive.")

        # Revoke old token
        self.refresh_token_repository.revoke(stored_token)

        self.audit_service.log(
            action="TOKEN_REFRESH",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return self._issue_tokens(user)

    def logout(
        self,
        current_user: User,
        request: RefreshTokenRequest,
        access_token: str,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Logout user by revoking the refresh token.
        """

        payload = decode_token(request.refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token.")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        stored_token = self.refresh_token_repository.get_by_token(request.refresh_token)

        if stored_token is None:
            raise ValueError("Refresh token not found.")

        # Revoke entire token family on logout
        self.refresh_token_repository.revoke_family(stored_token.family_id)

        # Decode access token
        access_payload = decode_token(access_token)

        if access_payload is None:
            raise ValueError("Invalid access token.")

        jti = access_payload.get("jti")

        if jti is None:
            raise ValueError("Missing token identifier.")

        exp = access_payload.get("exp")

        remaining_ttl = max(
            0,
            int(exp - datetime.now(UTC).timestamp()),
        )

        self.cache.blacklist_token(
            jti,
            remaining_ttl,
        )

        self.audit_service.log(
            action="LOGOUT",
            success=True,
            user_id=current_user.id,
            ip_address=ip_address,
        )

        return MessageResponse(message="Logged out successfully.")

    def forgot_password(
        self,
        request: ForgotPasswordRequest,
        ip_address: str | None = None,
    ) -> ForgotPasswordResponse:
        """
        Generate a password reset token.
        """

        user = self.user_repository.get_by_email(request.email)

        if user is None:
            self.audit_service.log(
                action="PASSWORD_RESET_REQUEST",
                success=False,
                user_id=None,
                ip_address=ip_address,
            )
            return ForgotPasswordResponse(
                message="If the email exists, a password reset link has been sent."
            )

        reset_token = token_urlsafe(32)

        token = PasswordResetToken(
            token=reset_token,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )

        self.password_reset_repository.create(token)

        logger.info(
            "Password reset requested: %s",
            user.email,
        )

        self.audit_service.log(
            action="PASSWORD_RESET_REQUEST",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        reset_link = f"{settings.frontend_url}/api/v1/auth/reset-password?token={reset_token}"

        self.email_provider.send_password_reset_email(
            user.email,
            reset_link,
        )

        return ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent."
        )

    def reset_password(
        self,
        request: ResetPasswordRequest,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Reset a user's password using a reset token.
        """

        reset = self.password_reset_repository.get_by_token(request.token)

        if reset is None:
            self.audit_service.log(
                action="PASSWORD_RESET",
                success=False,
                user_id=None,
                ip_address=ip_address,
            )
            raise ValueError("Invalid reset token.")

        if reset.is_used:
            self.audit_service.log(
                action="PASSWORD_RESET",
                success=False,
                user_id=reset.user_id,
                ip_address=ip_address,
            )
            raise ValueError("Reset token already used.")

        # Normalize to UTC-aware for comparison
        exp = reset.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            self.audit_service.log(
                action="PASSWORD_RESET",
                success=False,
                user_id=reset.user_id,
                ip_address=ip_address,
            )
            raise ValueError("Reset token expired.")

        user = reset.user

        user.hashed_password = hash_password(request.new_password)

        self.user_repository.update(user)

        self.password_reset_repository.mark_used(reset)

        # Revoke all existing sessions after password reset
        self.refresh_token_repository.revoke_all_for_user(user.id)

        logger.info(
            "Password reset completed: %s",
            user.email,
        )

        self.audit_service.log(
            action="PASSWORD_RESET",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return MessageResponse(message="Password reset successful.")

    def change_password(
        self,
        current_user: User,
        request: ChangePasswordRequest,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Change the current user's password.
        """

        if not verify_password(
            request.current_password,
            current_user.hashed_password,
        ):
            self.audit_service.log(
                action="PASSWORD_CHANGE",
                success=False,
                user_id=current_user.id,
                ip_address=ip_address,
            )
            raise ValueError("Current password is incorrect.")

        current_user.hashed_password = hash_password(request.new_password)

        self.user_repository.update(current_user)

        # Revoke all refresh tokens for this user on password change
        self.refresh_token_repository.revoke_all_for_user(current_user.id)

        logger.info(
            "Password changed: %s",
            current_user.email,
        )

        self.audit_service.log(
            action="PASSWORD_CHANGE",
            success=True,
            user_id=current_user.id,
            ip_address=ip_address,
        )

        return MessageResponse(message="Password changed successfully.")

    def verify_email(
        self,
        token: str,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Verify user's email using verification token.
        """

        verification = self.email_verification_repository.get_by_token(token)

        if verification is None:
            self.audit_service.log(
                action="EMAIL_VERIFY",
                success=False,
                user_id=None,
                ip_address=ip_address,
            )
            raise ValueError("Invalid verification token.")

        if verification.is_used:
            self.audit_service.log(
                action="EMAIL_VERIFY",
                success=False,
                user_id=verification.user_id,
                ip_address=ip_address,
            )
            raise ValueError("Verification token already used.")

        exp = verification.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            self.audit_service.log(
                action="EMAIL_VERIFY",
                success=False,
                user_id=verification.user_id,
                ip_address=ip_address,
            )
            raise ValueError("Verification token expired.")

        user = verification.user

        user.is_verified = True

        self.user_repository.update(user)

        verification.is_used = True

        self.email_verification_repository.update(verification)

        self.audit_service.log(
            action="EMAIL_VERIFY",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        logger.info(
            "Email verified: %s",
            user.email,
        )

        return MessageResponse(message="Email verified successfully.")

    def resend_verification(
        self,
        request: ResendVerificationRequest,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Generate a new email verification token.
        """

        user = self.user_repository.get_by_email(request.email)

        if user is None:
            self.audit_service.log(
                action="EMAIL_RESEND",
                success=False,
                user_id=None,
                ip_address=ip_address,
            )
            return MessageResponse(
                message="If the email exists, a verification email has been sent."
            )

        if user.is_verified:
            self.audit_service.log(
                action="EMAIL_RESEND",
                success=False,
                user_id=user.id,
                ip_address=ip_address,
            )
            return MessageResponse(message="Email is already verified.")

        verification_token = token_urlsafe(32)

        verification = EmailVerificationToken(
            token=verification_token,
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )

        self.email_verification_repository.create(verification)

        logger.info(
            "Verification email resent: %s",
            user.email,
        )

        verification_link = (
            f"{settings.frontend_url}/api/v1/auth/verify-email?token={verification_token}"
        )

        self.email_provider.send_verification_email(
            user.email,
            verification_link,
        )

        return MessageResponse(message="Verification email sent.")

    def cleanup_expired_refresh_tokens(self) -> int:
        """
        Permanently delete expired refresh tokens.
        Returns the number of deleted rows.
        """
        deleted = self.refresh_token_repository.delete_expired()

        logger.info(
            "Cleaned up %d expired refresh tokens",
            deleted,
        )

        return deleted

    def _record_failed_attempt(
        self,
        fail_key: str,
        max_failures: int,
        lockout_seconds: int,
    ) -> None:
        """
        Increment failed login counter and lock account if threshold reached.
        """
        current = self.cache.get(fail_key)

        if current is None:
            self.cache.set(fail_key, "1", ttl=lockout_seconds)
            return

        try:
            count = int(current)
        except (ValueError, TypeError):
            count = 0

        count += 1
        self.cache.set(fail_key, str(count), ttl=lockout_seconds)

        if count >= max_failures:
            self.cache.set(f"login_lock:{fail_key.split(':', 1)[1]}", "1", ttl=lockout_seconds)

    # ========================================================================
    # TOTP 2FA Methods
    # ========================================================================

    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret key."""
        return pyotp.random_base32()

    def generate_backup_codes(self, count: int = 8) -> tuple[list[str], list[str]]:
        """
        Generate backup codes.
        Returns (plaintext_codes, hashed_codes).
        Plaintext codes are shown to user once; hashes are stored.
        """
        plaintext = []
        hashed = []
        for _ in range(count):
            code = token_urlsafe(4)  # 8-char code
            plaintext.append(code)
            hashed.append(hashlib.sha256(code.encode()).hexdigest())
        return plaintext, hashed

    def _build_qr_code(self, secret: str, email: str) -> str:
        """Generate a base64 data URI QR code for TOTP enrollment."""
        totp_uri = pyotp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name="AuthForge",
        )
        img = qrcode.make(totp_uri)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def enable_totp(
        self,
        user: User,
        ip_address: str | None = None,
    ) -> TotpEnableResponse:
        """
        Initiate TOTP 2FA enrollment.
        Creates an unverified TOTP device and returns secret + QR + backup codes.
        The device must be confirmed via verify_totp_setup before it becomes active.
        """

        existing = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)
        if existing is not None and existing.is_verified:
            raise ValueError("Two-factor authentication is already enabled.")

        secret = self.generate_totp_secret()
        plaintext_codes, hashed_codes = self.generate_backup_codes()
        qr_code = self._build_qr_code(secret, user.email)

        device = TotpDevice(
            user_id=user.id,
            secret_key=secret,
            is_verified=False,
            backup_codes=hashed_codes,
        )

        TotpDeviceRepository(self.user_repository.db).create(device)

        self.audit_service.log(
            action="TOTP_ENROLLMENT_STARTED",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return TotpEnableResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=plaintext_codes,
        )

    def verify_totp_setup(
        self,
        user: User,
        token: str,
        ip_address: str | None = None,
    ) -> TotpVerifyResponse:
        """
        Verify the initial TOTP token during enrollment.
        Marks the TOTP device as verified (active 2FA).
        """

        device = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)

        if device is None:
            raise ValueError("No TOTP enrollment found. Call enable first.")

        if device.is_verified:
            raise ValueError("Two-factor authentication is already active.")

        totp = pyotp.TOTP(device.secret_key)

        if not totp.verify(token):
            self.audit_service.log(
                action="TOTP_SETUP_FAILED",
                success=False,
                user_id=user.id,
                ip_address=ip_address,
            )
            raise ValueError("Invalid TOTP token.")

        device.is_verified = True
        TotpDeviceRepository(self.user_repository.db).update(device)

        self.audit_service.log(
            action="TOTP_ENABLED",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return TotpVerifyResponse(
            message="Two-factor authentication enabled.",
            verified=True,
        )

    def disable_totp(
        self,
        user: User,
        token: str,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """
        Disable TOTP 2FA after verifying a current TOTP token.
        """

        device = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)

        if device is None or not device.is_verified:
            raise ValueError("Two-factor authentication is not enabled.")

        totp = pyotp.TOTP(device.secret_key)

        if not totp.verify(token):
            self.audit_service.log(
                action="TOTP_DISABLE_FAILED",
                success=False,
                user_id=user.id,
                ip_address=ip_address,
            )
            raise ValueError("Invalid TOTP token.")

        TotpDeviceRepository(self.user_repository.db).delete(device)

        self.audit_service.log(
            action="TOTP_DISABLED",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return MessageResponse(message="Two-factor authentication disabled.")

    def get_totp_status(
        self,
        user: User,
    ) -> TotpStatusResponse:
        """Return whether TOTP 2FA is enabled for the user."""

        device = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)

        enabled = device is not None and device.is_verified
        has_backup = enabled and device.backup_codes is not None and len(device.backup_codes) > 0

        return TotpStatusResponse(
            enabled=enabled,
            has_backup_codes=has_backup,
        )

    def verify_totp_login(
        self,
        user: User,
        token: str,
        ip_address: str | None = None,
    ) -> TotpVerifyResponse:
        """
        Verify a TOTP token during the login second step.
        Also accepts backup codes (single-use).
        """

        device = TotpDeviceRepository(self.user_repository.db).get_by_user(user.id)

        if device is None or not device.is_verified:
            raise ValueError("Two-factor authentication is not enabled.")

        totp = pyotp.TOTP(device.secret_key)

        if totp.verify(token):
            self.audit_service.log(
                action="TOTP_LOGIN_SUCCESS",
                success=True,
                user_id=user.id,
                ip_address=ip_address,
            )
            return TotpVerifyResponse(
                message="Two-factor verification successful.",
                verified=True,
            )

        # Try backup codes (single-use)
        if device.backup_codes:
            code_hash = hashlib.sha256(token.encode()).hexdigest()
            if code_hash in device.backup_codes:
                # Remove used backup code
                device.backup_codes.remove(code_hash)
                TotpDeviceRepository(self.user_repository.db).update(device)

                self.audit_service.log(
                    action="TOTP_BACKUP_CODE_USED",
                    success=True,
                    user_id=user.id,
                    ip_address=ip_address,
                )
                return TotpVerifyResponse(
                    message="Two-factor verification successful (backup code).",
                    verified=True,
                )

        self.audit_service.log(
            action="TOTP_LOGIN_FAILED",
            success=False,
            user_id=user.id,
            ip_address=ip_address,
        )
        raise ValueError("Invalid TOTP token or backup code.")

    # ========================================================================
    # API Key Methods
    # ========================================================================

    def create_api_key(
        self,
        user: User,
        name: str,
        scopes: list[str] | None = None,
        expires_in_days: int | None = None,
        ip_address: str | None = None,
    ) -> ApiKeyCreateResponse:
        """
        Create a new API key for a user.
        Returns the plaintext key only once (shown to user at creation time).
        """

        # Generate the actual key value
        api_key_value = f"ak_{token_urlsafe(32)}"
        key_prefix = api_key_value[:8]
        key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()

        # Compute expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        api_key = ApiKey(
            user_id=user.id,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            scopes=scopes,
            expires_at=expires_at,
        )

        created = self.api_key_repository.create(api_key)

        self.audit_service.log(
            action="API_KEY_CREATED",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return ApiKeyCreateResponse(
            id=str(created.id),
            name=created.name,
            key_prefix=created.key_prefix,
            scopes=created.scopes,
            expires_at=created.expires_at.isoformat() if created.expires_at else None,
            api_key=api_key_value,
        )

    def list_api_keys(
        self,
        user: User,
    ) -> list[ApiKeyResponse]:
        """List all API keys for a user (without exposing key values)."""

        keys = self.api_key_repository.get_all_for_user(user.id)

        return [
            ApiKeyResponse(
                id=str(k.id),
                name=k.name,
                key_prefix=k.key_prefix,
                scopes=k.scopes,
                expires_at=k.expires_at.isoformat() if k.expires_at else None,
                last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
                is_revoked=k.is_revoked,
                created_at=k.created_at.isoformat(),
            )
            for k in keys
        ]

    def revoke_api_key(
        self,
        user: User,
        api_key_id: str,
        ip_address: str | None = None,
    ) -> MessageResponse:
        """Revoke an API key."""

        from uuid import UUID

        try:
            key_id = UUID(api_key_id)
        except ValueError:
            raise ValueError("Invalid API key ID.")

        api_key = self.api_key_repository.get_by_id(key_id)

        if api_key is None:
            raise ValueError("API key not found.")

        if api_key.user_id != user.id:
            raise ValueError("API key not found.")

        if api_key.is_revoked:
            raise ValueError("API key already revoked.")

        api_key.is_revoked = True
        self.api_key_repository.update(api_key)

        self.audit_service.log(
            action="API_KEY_REVOKED",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
        )

        return MessageResponse(message="API key revoked.")

    def verify_api_key(
        self,
        api_key_value: str,
    ) -> User | None:
        """
        Verify an API key value and return the associated user.
        Returns None if the key is invalid, revoked, or expired.
        Updates last_used_at on success.
        """

        if not api_key_value or not api_key_value.startswith("ak_"):
            return None

        key_prefix = api_key_value[:8]
        key_hash = hashlib.sha256(api_key_value.encode()).hexdigest()

        candidates = self.api_key_repository.get_by_key_prefix(key_prefix)

        for candidate in candidates:
            if candidate.key_hash != key_hash:
                continue
            if candidate.is_revoked:
                return None
            if candidate.expires_at and candidate.expires_at < datetime.now(UTC):
                return None

            # Found valid key - update last_used_at
            candidate.last_used_at = datetime.now(UTC)
            self.api_key_repository.update(candidate)

            # Load the user
            user = self.user_repository.get_by_id(candidate.user_id)
            if user is None or not user.is_active:
                return None

            return user

        return None
