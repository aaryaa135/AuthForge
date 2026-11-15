from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog


class AuditRepository:
    """
    Handles database operations for audit logs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        audit_log: AuditLog,
    ) -> AuditLog:
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def get_all(self) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def get_paginated(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        action: str | None = None,
        user_id=None,
        success: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[AuditLog], int]:
        """
        Return paginated audit logs with optional search/action/user/success filters and sorting.
        """
        base = select(AuditLog)

        if search:
            like = f"%{search}%"
            base = base.where(AuditLog.action.ilike(like))

        if action:
            base = base.where(AuditLog.action == action)

        if user_id is not None:
            base = base.where(AuditLog.user_id == user_id)

        if success is not None:
            base = base.where(AuditLog.success == success)

        total = self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

        order_column = getattr(AuditLog, sort_by, AuditLog.created_at)
        if sort_order.lower() == "asc":
            base = base.order_by(order_column.asc())
        else:
            base = base.order_by(order_column.desc())

        base = base.offset(offset).limit(limit)
        items = list(self.db.scalars(base).all())
        return items, total

    def get_by_user(
        self,
        user_id,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc())
        )

        return list(self.db.scalars(stmt).all())
