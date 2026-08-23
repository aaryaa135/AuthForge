from datetime import UTC, datetime, timedelta
from secrets import token_urlsafe

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
from app.modules.auth.models import EmailVerificationToken, PasswordResetToken, RefreshToken
from app.modules.auth.repository import (
    EmailVerificationRepository,
    PasswordResetRepository,
    RefreshTokenRepository,
)
from app.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
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
        email_provider: EmailProvider,
        audit_service: AuditService,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.refresh_token_repository = refresh_token_repository
        self.password_reset_repository = password_reset_repository
        self.email_verification_repository = email_verification_repository
        self.email_provider = email_provider
        self.cache = CacheService()
        self.audit_service = audit_service

    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        """

        # Check email
        if self.user_repository.get_by_email(user_data.email):
            raise ValueError("Email already registered.")

        # Check username
        if self.user_repository.get_by_username(user_data.username):
            raise ValueError("Username already taken.")

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
            f"{settings.frontend_url}/api/v1/auth/verify-email"
            f"?token={verification_token}"
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

        refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(UTC)
            + timedelta(days=settings.refresh_token_expire_days),
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
    ) -> TokenResponse:
        """
        Authenticate user using email or username.
        """

        if "@" in identifier:
            user = self.user_repository.get_by_email(identifier)
        else:
            user = self.user_repository.get_by_username(identifier)

        if user is None:
            logger.warning(
                "Invalid login attempt: %s",
                identifier,
            )
            raise ValueError("Invalid credentials.")

        if not user.is_active:
            raise ValueError("User account is inactive.")

        if not verify_password(
            password,
            user.hashed_password,
        ):
            logger.warning(
                "Invalid login attempt: %s",
                identifier,
            )
            raise ValueError("Invalid credentials.")

        if settings.require_email_verification and not user.is_verified:
            raise ValueError("Email not verified. Please verify your email first.")

        logger.info(
            "User logged in: %s",
            user.email,
        )

        self.audit_service.log(
            action="LOGIN",
            success=True,
            user_id=user.id,
        )

        return self._issue_tokens(user)

    def refresh_tokens(
        self,
        request: RefreshTokenRequest,
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

        # Check revocation
        if stored_token.is_revoked:
            raise ValueError("Refresh token revoked.")

        # Revoke old token
        self.refresh_token_repository.revoke(stored_token)

        return self._issue_tokens(stored_token.user)

    def logout(
        self,
        current_user: User,
        request: RefreshTokenRequest,
        access_token: str,
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

        if stored_token.is_revoked:
            raise ValueError("Refresh token already revoked.")

        self.refresh_token_repository.revoke(stored_token)

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
        )

        return MessageResponse(message="Logged out successfully.")

    def forgot_password(
        self,
        request: ForgotPasswordRequest,
    ) -> ForgotPasswordResponse:
        """
        Generate a password reset token.
        """

        user = self.user_repository.get_by_email(request.email)

        if user is None:
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

        reset_link = (
            f"{settings.frontend_url}/api/v1/auth/reset-password" f"?token={reset_token}"
        )

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
    ) -> MessageResponse:
        """
        Reset a user's password using a reset token.
        """

        reset = self.password_reset_repository.get_by_token(request.token)

        if reset is None:
            raise ValueError("Invalid reset token.")

        if reset.is_used:
            raise ValueError("Reset token already used.")

        # Normalize to UTC-aware for comparison
        exp = reset.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            raise ValueError("Reset token expired.")

        user = reset.user

        user.hashed_password = hash_password(request.new_password)

        self.user_repository.update(user)

        self.password_reset_repository.mark_used(reset)

        logger.info(
            "Password reset completed: %s",
            user.email,
        )

        self.audit_service.log(
            action="PASSWORD_RESET",
            success=True,
            user_id=user.id,
        )

        return MessageResponse(message="Password reset successful.")

    def change_password(
        self,
        current_user: User,
        request: ChangePasswordRequest,
    ) -> MessageResponse:
        """
        Change the current user's password.
        """

        if not verify_password(
            request.current_password,
            current_user.hashed_password,
        ):
            raise ValueError("Current password is incorrect.")

        current_user.hashed_password = hash_password(request.new_password)

        self.user_repository.update(current_user)

        logger.info(
            "Password changed: %s",
            current_user.email,
        )

        self.audit_service.log(
            action="PASSWORD_CHANGE",
            success=True,
            user_id=current_user.id,
        )

        return MessageResponse(message="Password changed successfully.")

    def verify_email(
        self,
        token: str,
    ) -> MessageResponse:
        """
        Verify user's email using verification token.
        """

        verification = self.email_verification_repository.get_by_token(token)

        if verification is None:
            raise ValueError("Invalid verification token.")

        if verification.is_used:
            raise ValueError("Verification token already used.")

        exp = verification.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if exp < datetime.now(UTC):
            raise ValueError("Verification token expired.")

        user = verification.user

        user.is_verified = True

        self.user_repository.update(user)

        verification.is_used = True

        self.email_verification_repository.update(verification)

        logger.info(
            "Email verified: %s",
            user.email,
        )

        return MessageResponse(message="Email verified successfully.")

    def resend_verification(
        self,
        request: ResendVerificationRequest,
    ) -> MessageResponse:
        """
        Generate a new email verification token.
        """

        user = self.user_repository.get_by_email(request.email)

        if user is None:
            return MessageResponse(
                message="If the email exists, a verification email has been sent."
            )

        if user.is_verified:
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
            f"{settings.frontend_url}/api/v1/auth/verify-email"
            f"?token={verification_token}"
        )

        self.email_provider.send_verification_email(
            user.email,
            verification_link,
        )

        return MessageResponse(message="Verification email sent.")
