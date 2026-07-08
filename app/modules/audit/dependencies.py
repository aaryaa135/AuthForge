from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.audit.repository import AuditRepository


def get_audit_repository(
    db: Session = Depends(get_db),
):
    return AuditRepository(db)
