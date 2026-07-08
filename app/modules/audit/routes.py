from fastapi import APIRouter, Depends

from app.modules.audit.dependencies import get_audit_repository
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogResponse
from app.modules.users.models import User
from app.shared.dependencies import get_admin_user

router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get(
    "/",
    response_model=list[AuditLogResponse],
)
def get_audit_logs(
    current_user: User = Depends(get_admin_user),
    repository: AuditRepository = Depends(get_audit_repository),
):
    return repository.get_all()
