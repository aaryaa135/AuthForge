from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import (
    ApiKeyRepository,
    RefreshTokenRepository,
    TotpDeviceRepository,
    UserSessionRepository,
)
from app.modules.auth.service import AuthService
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository


def _make_user(db, email="cleanup@example.com", username="cleanupuser"):
    role = RoleRepository(db).get_by_name("User")
    if role is None:
        from app.modules.roles.models import Role

        role = Role(name="User", description="default")
        db.add(role)
        db.commit()
        db.refresh(role)
    user = User(
        email=email,
        username=username,
        hashed_password="hashed",
        role_id=role.id,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_cleanup_expired_refresh_tokens_deletes_only_expired():
    db = SessionLocal()
    try:
        user = _make_user(db)
        repo = RefreshTokenRepository(db)

        # expired token
        expired = RefreshToken(
            token="expired-token",
            user_id=user.id,
            expires_at=datetime.now(UTC) - timedelta(days=1),
            is_revoked=False,
        )
        # active token
        active = RefreshToken(
            token="active-token",
            user_id=user.id,
            expires_at=datetime.now(UTC) + timedelta(days=7),
            is_revoked=False,
        )
        db.add(expired)
        db.add(active)
        db.commit()

        service = AuthService(
            user_repository=UserRepository(db),
            role_repository=RoleRepository(db),
            refresh_token_repository=repo,
            password_reset_repository=None,
            email_verification_repository=None,
            totp_device_repository=TotpDeviceRepository(db),
            api_key_repository=ApiKeyRepository(db),
            user_session_repository=UserSessionRepository(db),
            email_provider=None,
            audit_service=None,
        )

        deleted = service.cleanup_expired_refresh_tokens()

        assert deleted == 1

        assert repo.get_by_token("expired-token") is None
        assert repo.get_by_token("active-token") is not None
    finally:
        db.close()
