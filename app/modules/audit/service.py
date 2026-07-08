from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditRepository


class AuditService:
    """
    Handles audit logging.
    """

    def __init__(
        self,
        repository: AuditRepository,
    ):
        self.repository = repository

    def log(
        self,
        action: str,
        success: bool = True,
        user_id=None,
        ip_address: str | None = None,
    ):
        audit = AuditLog(
            action=action,
            success=success,
            user_id=user_id,
            ip_address=ip_address,
        )

        return self.repository.create(audit)
