from fastapi import APIRouter, Depends, Query

from app.modules.audit.dependencies import get_audit_repository
from app.modules.audit.repository import AuditRepository
from app.modules.audit.schemas import AuditLogResponse
from app.modules.users.models import User
from app.shared.dependencies import get_admin_user
from app.shared.pagination import PaginatedResponse

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit"],
)


@router.get(
    "/",
    response_model=PaginatedResponse[AuditLogResponse],
)
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_admin_user),
    repository: AuditRepository = Depends(get_audit_repository),
):
    offset = (page - 1) * page_size
    logs, total = repository.get_paginated(offset=offset, limit=page_size)
    items = [AuditLogResponse.model_validate(log) for log in logs]
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[AuditLogResponse](
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )
