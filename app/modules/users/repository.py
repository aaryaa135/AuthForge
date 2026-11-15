from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.cache.keys import RedisKeys
from app.cache.service import CacheService
from app.core.logger import logger
from app.modules.users.models import User


class UserRepository:
    """
    Handles all database operations related to users.
    """

    def __init__(self, db: Session):
        self.db = db
        self.cache = CacheService()

    def get_by_email(
        self,
        email: str,
    ):
        cache_key = RedisKeys.user_email(email)

        cached = self.cache.get_json(cache_key)

        if cached:
            logger.info("Cache HIT: %s", cache_key)
            return self.db.get(User, UUID(cached["id"]))

        logger.info("Cache MISS: %s", cache_key)

        stmt = select(User).where(User.email == email).options(joinedload(User.role))

        user = self.db.execute(stmt).scalar_one_or_none()

        if user:
            self.cache.set_json(
                cache_key,
                {"id": str(user.id)},
                ttl=300,
            )

        return user

    def get_by_username(
        self,
        username: str,
    ):
        cache_key = RedisKeys.user_username(username)

        cached = self.cache.get_json(cache_key)

        if cached:
            logger.info("Cache HIT: %s", cache_key)
            return self.db.get(User, UUID(cached["id"]))

        logger.info("Cache MISS: %s", cache_key)

        stmt = select(User).where(User.username == username).options(joinedload(User.role))

        user = self.db.execute(stmt).scalar_one_or_none()

        if user:
            self.cache.set_json(
                cache_key,
                {"id": str(user.id)},
                ttl=300,
            )

        return user

    def get_by_id(self, user_id: UUID | str) -> User | None:
        stmt = select(User).where(User.id == user_id).options(joinedload(User.role))
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
        stmt = select(User).options(joinedload(User.role)).order_by(User.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_paginated(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """
        Return paginated users with optional search, role, active filters and sorting.
        """
        base = select(User).options(joinedload(User.role))

        if search:
            like = f"%{search}%"
            base = base.where(
                or_(
                    User.email.ilike(like),
                    User.username.ilike(like),
                )
            )

        if role:
            base = base.where(User.role.has(name=role))

        if is_active is not None:
            base = base.where(User.is_active == is_active)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        order_column = getattr(User, sort_by, User.created_at)
        if sort_order.lower() == "asc":
            base = base.order_by(order_column.asc())
        else:
            base = base.order_by(order_column.desc())

        base = base.offset(offset).limit(limit)
        items = list(self.db.scalars(base).all())
        return items, total

    def update(self, user: User) -> User:
        self.db.commit()
        self.cache.delete(RedisKeys.user_email(user.email))

        self.cache.delete(RedisKeys.user_username(user.username))
        self.db.refresh(user)
        return user
