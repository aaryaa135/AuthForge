from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.auth.models import RefreshToken


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
        stmt = select(RefreshToken).where(
            RefreshToken.token == token
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke(self, token: RefreshToken) -> None:
        token.is_revoked = True
        self.db.commit()