from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.roles.models import Role


class RoleRepository:
    """
    Handles database operations related to roles.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return self.db.execute(stmt).scalar_one_or_none()
