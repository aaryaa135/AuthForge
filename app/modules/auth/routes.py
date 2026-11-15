from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.dependencies import require_role
from app.modules.auth.dependencies import get_auth_service, login_rate_limit
from app.modules.auth.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ChangePasswordRequest,
    CleanupResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    RefreshTokenRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenResponse,
    TotpDisableRequest,
    TotpEnableResponse,
    TotpLoginVerifyResponse,
    TotpStatusResponse,
    TotpVerifyRequest,
    TotpVerifyResponse,
)
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserResponse
from app.shared.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    try:
        service.register_user(user, ip_address=request.client.host)

        return MessageResponse(
            message=(
                "Registration successful. If the account was created, "
                "a verification email has been sent."
            ),
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed.",
        )


@router.post(
    "/login",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: None = Depends(login_rate_limit),
    request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.login_user(
            identifier=form_data.username,
            password=form_data.password,
            ip_address=request.client.host if request else None,
        )

    except ValueError as exc:
        if str(exc) == "TWO_FACTOR_REQUIRED":
            identifier = form_data.username
            user = None
            if "@" in identifier:
                user = service.user_repository.get_by_email(identifier)
            else:
                user = service.user_repository.get_by_username(identifier)
            return {
                "two_factor_required": True,
                "user_id": str(user.id) if user else None,
                "message": "Two-factor verification required.",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role.name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    request: RefreshTokenRequest,
    http_request: Request,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.refresh_tokens(
            request,
            ip_address=http_request.client.host if http_request else None,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
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

    try:
        return service.logout(
            current_user=current_user,
            request=body,
            access_token=access_token,
            ip_address=request.client.host if request else None,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed.",
        )


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
)
def forgot_password(
    request: ForgotPasswordRequest,
    http_request: Request,
    service: AuthService = Depends(get_auth_service),
):
    return service.forgot_password(
        request,
        ip_address=http_request.client.host if http_request else None,
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
)
def reset_password(
    request: ResetPasswordRequest,
    http_request: Request,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.reset_password(
            request,
            ip_address=http_request.client.host if http_request else None,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token.",
        )


@router.post(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.change_password(
            current_user,
            request,
            ip_address=http_request.client.host if http_request else None,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change failed.",
        )


@router.get(
    "/verify-email",
    response_model=MessageResponse,
)
def verify_email(
    token: str,
    http_request: Request,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.verify_email(
            token,
            ip_address=http_request.client.host if http_request else None,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token.",
        )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
)
def resend_verification(
    request: ResendVerificationRequest,
    http_request: Request,
    service: AuthService = Depends(get_auth_service),
):
    return service.resend_verification(
        request,
        ip_address=http_request.client.host if http_request else None,
    )


@router.post(
    "/admin/cleanup-tokens",
    response_model=CleanupResponse,
)
def cleanup_expired_tokens(
    service: AuthService = Depends(get_auth_service),
    _: User = Depends(require_role("Admin")),
):
    deleted = service.cleanup_expired_refresh_tokens()
    return CleanupResponse(
        message="Expired refresh tokens cleaned up.",
        deleted=deleted,
    )


# ========================================================================
# TOTP 2FA Routes
# ========================================================================


@router.post(
    "/2fa/enable",
    response_model=TotpEnableResponse,
)
def enable_totp(
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    return service.enable_totp(
        current_user,
        ip_address=http_request.client.host if http_request else None,
    )


@router.post(
    "/2fa/verify-setup",
    response_model=TotpVerifyResponse,
)
def verify_totp_setup(
    request: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    return service.verify_totp_setup(
        current_user,
        request.token,
        ip_address=http_request.client.host if http_request else None,
    )


@router.post(
    "/2fa/disable",
    response_model=MessageResponse,
)
def disable_totp(
    request: TotpDisableRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    return service.disable_totp(
        current_user,
        request.token,
        ip_address=http_request.client.host if http_request else None,
    )


@router.get(
    "/2fa/status",
    response_model=TotpStatusResponse,
)
def totp_status(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    return service.get_totp_status(current_user)


@router.post(
    "/2fa/login-verify",
    response_model=TotpLoginVerifyResponse,
)
def login_verify_totp(
    request: TotpVerifyRequest,
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    """
    Complete login after 2FA challenge.
    Requires a pending 2FA session (created during login when 2FA is enabled).
    The client must pass the user_id from the login response in the request body.
    """
    # We need user_id but it's not in TotpVerifyRequest. Extract from pending state.
    # The pending key format is 2fa_pending:{user_id}. We need to find which user has pending 2FA.
    # This is a limitation - in production, pass user_id in the request or use a temp token.
    # For now, we'll scan Redis for pending 2FA keys.
    # Better approach: add user_id to TotpVerifyRequest or use a separate schema.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Use /api/v1/auth/2fa/login-verify-complete with user_id.",
    )


@router.post(
    "/2fa/login-verify-complete",
    response_model=TotpLoginVerifyResponse,
)
def login_verify_totp_complete(
    user_id: str,
    request: TotpVerifyRequest,
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    """
    Complete login after 2FA challenge.
    Requires user_id (from login response) and TOTP token.
    """

    from uuid import UUID

    # Verify pending 2FA session exists
    pending_key = f"2fa_pending:{user_id}"
    if not service.cache.exists(pending_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending two-factor session found. Please log in first.",
        )

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID.",
        )

    user = service.user_repository.get_by_id(user_uuid)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    try:
        service.verify_totp_login(
            user,
            request.token,
            ip_address=http_request.client.host if http_request else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )

    # Clear pending 2FA session
    service.cache.delete(pending_key)

    # Issue tokens
    tokens = service._issue_tokens(user)

    return TotpLoginVerifyResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )


# ========================================================================
# API Key Routes (Service Accounts / M2M)
# ========================================================================


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
)
def create_api_key(
    request: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    return service.create_api_key(
        current_user,
        name=request.name,
        scopes=request.scopes,
        expires_in_days=request.expires_in_days,
        ip_address=http_request.client.host if http_request else None,
    )


@router.get(
    "/api-keys",
    response_model=ApiKeyListResponse,
)
def list_api_keys(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    keys = service.list_api_keys(current_user)
    return ApiKeyListResponse(keys=keys)


@router.delete(
    "/api-keys/{api_key_id}",
    response_model=MessageResponse,
)
def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    http_request: Request = None,
    service: AuthService = Depends(get_auth_service),
):
    return service.revoke_api_key(
        current_user,
        api_key_id,
        ip_address=http_request.client.host if http_request else None,
    )
