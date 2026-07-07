from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.auth.repository import (
    RefreshTokenRepository,
    PasswordResetRepository,
    EmailVerificationRepository,
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

    return AuthService(
        user_repository=UserRepository(db),
        role_repository=RoleRepository(db),
        refresh_token_repository=RefreshTokenRepository(db),
        password_reset_repository=PasswordResetRepository(db),
        email_verification_repository=EmailVerificationRepository(db),
        email_provider=get_email_provider(),
    )
