from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.db.session import get_db
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UpdateUserRoleRequest, UpdateUserStatusRequest, UserResponse
from app.modules.users.service import UserService
from app.shared.pagination import PaginatedResponse

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, description="Search by email or username"),
    role: str | None = Query(None, description="Filter by role name"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("Admin")),
):
    repo = UserRepository(db)
    offset = (page - 1) * page_size
    users, total = repo.get_paginated(
        offset=offset,
        limit=page_size,
        search=search,
        role=role,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items = [
        UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
        for user in users
    ]
    pages = (total + page_size - 1) // page_size if total else 0
    return PaginatedResponse[UserResponse](
        items=items, total=total, page=page, page_size=page_size, pages=pages
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("Admin")),
):
    service = UserService(
        UserRepository(db),
    )

    try:
        return service.get_user(user_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify your own role.",
        )

    service = UserService(
        UserRepository(db),
    )

    role_repository = RoleRepository(db)

    try:
        return service.update_role(
            user_id=user_id,
            role_name=request.role,
            role_repository=role_repository,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: UUID,
    request: UpdateUserStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Admin")),
):
    if current_user.id == user_id and not request.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate your own account.",
        )

    service = UserService(
        UserRepository(db),
    )

    try:
        return service.update_status(
            user_id=user_id,
            is_active=request.is_active,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
