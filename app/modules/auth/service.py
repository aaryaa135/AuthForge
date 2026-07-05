from app.core.security import hash_password
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate
from datetime import datetime, timedelta, timezone

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.core.security import verify_password
from app.modules.auth.models import RefreshToken
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
)

class AuthService:
    """
    Handles authentication business logic.
    """

    def __init__(
        self,
        user_repository,
        role_repository,
        refresh_token_repository,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.refresh_token_repository = refresh_token_repository
        self.user_repository = user_repository
        self.role_repository = role_repository

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

        if not verify_password(
            password,
            user.hashed_password,
        ):
            raise ValueError("Invalid credentials.")

        access_token = create_access_token(
            subject=str(user.id),
        )

        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        refresh = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=7),
        )

        self.refresh_token_repository.create(refresh)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )