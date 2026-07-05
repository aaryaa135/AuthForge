from app.core.security import hash_password
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from datetime import datetime, timedelta, timezone
from app.core.security import verify_password
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import RefreshTokenRepository
from app.core.config import settings

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    MessageResponse,
)

class AuthService:
    """
    Handles authentication business logic.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        refresh_token_repository: RefreshTokenRepository,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.refresh_token_repository = refresh_token_repository

    def register_user(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        """

        # Check email
        if self.user_repository.get_by_email(user_data.email):
            raise ValueError("Email already registered.")

        # Check username
        if self.user_repository.get_by_username(user_data.username):
            raise ValueError("Username already taken.")

        # Default role
        default_role = self.role_repository.get_by_name("User")

        if default_role is None:
            raise ValueError("Default role not found.")

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hash_password(user_data.password),
            role_id=default_role.id,
            is_active=True,
            is_verified=False,
        )

        return self.user_repository.create(user)
    

    def _issue_tokens(
        self,
        user: User,
    ) -> TokenResponse:
        """
        Generate and persist new access and refresh tokens.
        """

        access_token = create_access_token(
            subject=str(user.id),
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.refresh_token_expire_days
            )
        )


        self.refresh_token_repository.create(refresh)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )
    
    def login_user(
        self,
        identifier: str,
        password: str,
    ) -> TokenResponse:
        """
        Authenticate user using email or username.
        """

        if "@" in identifier:
            user = self.user_repository.get_by_email(identifier)
        else:
            user = self.user_repository.get_by_username(identifier)

        if user is None:
            raise ValueError("Invalid credentials.")

        if not user.is_active:
            raise ValueError("User account is inactive.")

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise ValueError("Invalid credentials.")

        return self._issue_tokens(user)
    
    def refresh_tokens(
        self,
        request: RefreshTokenRequest,
    ) -> TokenResponse:
        """
        Rotate refresh token and issue a new access token.
        """

        # Decode JWT
        payload = decode_token(request.refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token.")

        # Ensure it's actually a refresh token
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        # Find token in DB
        stored_token = self.refresh_token_repository.get_by_token(
            request.refresh_token
        )

        if stored_token is None:
            raise ValueError("Refresh token not found.")

        # Check revocation
        if stored_token.is_revoked:
            raise ValueError("Refresh token revoked.")

        # Revoke old token
        self.refresh_token_repository.revoke(stored_token)

        return self._issue_tokens(stored_token.user)
    
    def logout(
        self,
        request: RefreshTokenRequest,
    ) -> MessageResponse:
        """
        Logout user by revoking the refresh token.
        """

        payload = decode_token(request.refresh_token)

        if payload is None:
            raise ValueError("Invalid refresh token.")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        stored_token = self.refresh_token_repository.get_by_token(
            request.refresh_token
        )

        if stored_token is None:
            raise ValueError("Refresh token not found.")

        if stored_token.is_revoked:
            raise ValueError("Refresh token already revoked.")

        self.refresh_token_repository.revoke(stored_token)

        return MessageResponse(
            message="Logged out successfully."
        )
    