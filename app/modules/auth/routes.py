from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.auth.service import AuthService
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
from app.modules.auth.schemas import ResendVerificationRequest
from app.modules.auth.dependencies import get_auth_service
from fastapi import Request
from app.modules.auth.dependencies import login_rate_limit


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
    service: AuthService = Depends(get_auth_service),
):
    try:
        created_user = service.register_user(user)

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

    except Exception as exc:
        import traceback

        traceback.print_exc()

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
    _: None = Depends(login_rate_limit),
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.login_user(
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
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.refresh_tokens(request)

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
    body: RefreshTokenRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    authorization = request.headers.get("Authorization")

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header.",
        )

    access_token = authorization.removeprefix("Bearer ").strip()

    return service.logout(
        current_user=current_user,
        request=body,
        access_token=access_token,
    )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.forgot_password(request)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    request: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.reset_password(request)


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return service.change_password(
        current_user,
        request,
    )


@router.get(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    token: str,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.verify_email(token)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
def resend_verification(
    request: ResendVerificationRequest,
    service: AuthService = Depends(get_auth_service),
):
    return service.resend_verification(request)
