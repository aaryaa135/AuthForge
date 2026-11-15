from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type constant


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
    access_token: str


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class CleanupResponse(BaseModel):
    message: str
    deleted: int


class TotpEnableResponse(BaseModel):
    secret: str
    qr_code: str  # base64 data URI
    backup_codes: list[str]


class TotpVerifyRequest(BaseModel):
    token: str


class TotpVerifyResponse(BaseModel):
    message: str
    verified: bool


class TotpDisableRequest(BaseModel):
    token: str


class TotpStatusResponse(BaseModel):
    enabled: bool
    has_backup_codes: bool


class TotpLoginVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token type constant


# ========================================================================
# API Key Schemas
# ========================================================================


class ApiKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] | None = None
    expires_in_days: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str] | None
    expires_at: str | None
    last_used_at: str | None
    is_revoked: bool
    created_at: str


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    scopes: list[str] | None
    expires_at: str | None
    # Only shown once on creation
    api_key: str


class ApiKeyListResponse(BaseModel):
    keys: list[ApiKeyResponse]
