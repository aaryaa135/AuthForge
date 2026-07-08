from sqlalchemy import select
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

    def get_by_user(
        self,
        user_id,
    ) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
        )

        return list(self.db.scalars(stmt).all())
