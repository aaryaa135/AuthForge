from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.service import AuthService
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate, UserResponse
from app.modules.users.models import User
from app.shared.dependencies import get_current_user
from fastapi.security import OAuth2PasswordRequestForm

from app.modules.auth.schemas import (
    TokenResponse,
    MessageResponse,
    RefreshTokenRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ChangePasswordRequest,
)
from app.modules.auth.repository import (
    RefreshTokenRepository,
    PasswordResetRepository,
)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    try:
        created_user = auth_service.register_user(user)

        print(created_user)
        print(type(created_user))
        print(created_user.role)

        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            username=created_user.username,
            role=created_user.role.name,
            is_active=created_user.is_active,
            is_verified=created_user.is_verified,
            created_at=created_user.created_at,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    try:
        return auth_service.login_user(
            identifier=form_data.username,
            password=form_data.password,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    try:
        return auth_service.refresh_tokens(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
)
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    try:
        return auth_service.logout(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    return service.forgot_password(request)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    return service.reset_password(request)


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(
        UserRepository(db),
        RoleRepository(db),
        RefreshTokenRepository(db),
        PasswordResetRepository(db),
    )

    return service.change_password(
        current_user,
        request,
    )
