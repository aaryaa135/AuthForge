from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.users.models import User

class UserRepository:
    """
    Handles all database operations related to users.
    """

    def __init__(self, db: Session):
        
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: UUID | str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_all(self) -> list[User]:
        """
        Return all users.
        """
        stmt = select(User).order_by(User.created_at.desc())
        return list(self.db.scalars(stmt).all())
    
    def update(self, user: User) -> User:
        """
        Persist changes to a user.
        """
        self.db.commit()
        self.db.refresh(user)
        return user