from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import RefreshToken
from app.modules.auth.models import PasswordResetToken
from app.modules.auth.models import EmailVerificationToken


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
        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token == token
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def mark_used(
        self,
        token: EmailVerificationToken,
    ):
        token.is_used = True
        self.db.commit()
        self.db.refresh(token)
        return token
