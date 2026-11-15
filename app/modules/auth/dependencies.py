from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import RateLimiter
from app.db.session import get_db
from app.modules.audit.repository import AuditRepository
from app.modules.audit.service import AuditService
from app.modules.auth.repository import (
    ApiKeyRepository,
    EmailVerificationRepository,
    PasswordResetRepository,
    RefreshTokenRepository,
    TotpDeviceRepository,
    UserSessionRepository,
)
from app.modules.auth.service import AuthService
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.providers.factory import get_email_provider


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    """
    Dependency provider for AuthService.
    """

    audit_service = AuditService(
        AuditRepository(db),
    )

    return AuthService(
        user_repository=UserRepository(db),
        role_repository=RoleRepository(db),
        refresh_token_repository=RefreshTokenRepository(db),
        password_reset_repository=PasswordResetRepository(db),
        email_verification_repository=EmailVerificationRepository(db),
        totp_device_repository=TotpDeviceRepository(db),
        api_key_repository=ApiKeyRepository(db),
        user_session_repository=UserSessionRepository(db),
        email_provider=get_email_provider(),
        audit_service=audit_service,
    )


def login_rate_limit(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    limiter = RateLimiter()

    key = f"login:{form_data.username}"

    if not limiter.allow_request(
        key=key,
        limit=5,
        window=60,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )


async def get_api_key_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate via X-API-Key header for service accounts.
    Returns the User associated with the API key.
    """

    api_key = request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header.",
        )

    user = service.verify_api_key(api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
        )

    return user
