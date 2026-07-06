from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService

from app.core.dependencies import require_role
from app.modules.users.models import User

from uuid import UUID

from fastapi import HTTPException, status
from app.modules.roles.repository import RoleRepository
from app.modules.users.schemas import UpdateUserRoleRequest, UpdateUserStatusRequest

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/",
    response_model=list[UserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("Admin")),
):
    service = UserService(
        UserRepository(db),
    )

    return service.list_users()


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
    _: User = Depends(require_role("Admin")),
):
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
    _: User = Depends(require_role("Admin")),
):
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
