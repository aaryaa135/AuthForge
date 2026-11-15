from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.modules.auth.models import (
    ApiKey,
    EmailVerificationToken,
    PasswordResetToken,
    RefreshToken,
    TotpDevice,
    UserSession,
)


class RefreshTokenRepository:
    """
    Handles refresh token persistence.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, token: RefreshToken) -> RefreshToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke(self, token: RefreshToken) -> None:
        token.is_revoked = True
        self.db.commit()

    def delete(self, refresh_token: RefreshToken) -> None:
        """
        Remove a refresh token from the database.
        """
        self.db.delete(refresh_token)
        self.db.commit()

    def delete_expired(self) -> int:
        """
        Permanently delete refresh tokens whose expires_at is in the past,
        plus any revoked tokens regardless of expiry.
        Returns the number of deleted rows.
        """
        now = datetime.now(UTC)
        stmt = delete(RefreshToken).where(
            (RefreshToken.expires_at < now) | (RefreshToken.is_revoked == True)  # noqa: E712
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    def revoke_family(self, family_id) -> int:
        """
        Revoke all refresh tokens in a token family.
        Returns the number of revoked rows.
        """
        from sqlalchemy import update

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .where(RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    def revoke_all_for_user(self, user_id) -> int:
        """
        Revoke all refresh tokens for a user.
        Returns the number of revoked rows.
        """
        from sqlalchemy import update

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0


class PasswordResetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, token: PasswordResetToken):
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_token(self, token: str):
        stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(self, token: PasswordResetToken):
        self.db.commit()
        self.db.refresh(token)
        return token

    def mark_used(
        self,
        token: PasswordResetToken,
    ):
        token.is_used = True
        self.db.commit()
        self.db.refresh(token)
        return token


class EmailVerificationRepository:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create(
        self,
        token: EmailVerificationToken,
    ):
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_token(
        self,
        token: str,
    ):
        stmt = select(EmailVerificationToken).where(EmailVerificationToken.token == token)
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_used(
        self,
        token: EmailVerificationToken,
    ):
        token.is_used = True
        self.db.commit()
        self.db.refresh(token)
        return token

    def update(
        self,
        token: EmailVerificationToken,
    ):
        self.db.commit()
        self.db.refresh(token)
        return token


class TotpDeviceRepository:
    """
    Handles TOTP device persistence for 2FA.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        device: TotpDevice,
    ) -> TotpDevice:
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def get_by_user(
        self,
        user_id,
    ) -> TotpDevice | None:
        stmt = select(TotpDevice).where(TotpDevice.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def update(
        self,
        device: TotpDevice,
    ) -> TotpDevice:
        self.db.commit()
        self.db.refresh(device)
        return device

    def delete(
        self,
        device: TotpDevice,
    ) -> None:
        self.db.delete(device)
        self.db.commit()


class ApiKeyRepository:
    """
    Handles API key persistence for service accounts.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def get_by_id(self, api_key_id) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.id == api_key_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_key_prefix(self, key_prefix: str) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.key_prefix == key_prefix)
        return list(self.db.scalars(stmt).all())

    def get_all_for_user(self, user_id) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def update(self, api_key: ApiKey) -> ApiKey:
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def delete(self, api_key: ApiKey) -> None:
        self.db.delete(api_key)
        self.db.commit()


class UserSessionRepository:
    """
    Handles user session persistence for device/session management.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_jti(self, jti: str) -> UserSession | None:
        stmt = select(UserSession).where(UserSession.jti == jti)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_for_user(self, user_id) -> list[UserSession]:
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        return list(self.db.scalars(stmt).all())

    def get_active_for_user(self, user_id) -> list[UserSession]:
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_revoked == False,  # noqa: E712
        )
        return list(self.db.scalars(stmt).all())

    def revoke_by_jti(self, jti: str) -> bool:
        session = self.get_by_jti(jti)
        if session is None or session.is_revoked:
            return False
        session.is_revoked = True
        self.db.commit()
        self.db.refresh(session)
        return True

    def revoke_all_for_user(self, user_id) -> int:
        from sqlalchemy import update

        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    def revoke_all_except_for_user(self, user_id, exclude_jti: str) -> int:
        from sqlalchemy import update

        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.jti != exclude_jti)
            .where(UserSession.is_revoked == False)  # noqa: E712
            .values(is_revoked=True)
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    def update_last_active(self, jti: str) -> bool:
        session = self.get_by_jti(jti)
        if session is None or session.is_revoked:
            return False
        session.last_active_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(session)
        return True

    def delete(
        self,
        session: UserSession,
    ) -> None:
        self.db.delete(session)
        self.db.commit()
