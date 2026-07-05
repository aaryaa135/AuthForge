from app.core.security import hash_password
from app.modules.roles.repository import RoleRepository
from app.modules.users.models import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserCreate


class AuthService:
    """
    Handles authentication business logic.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ):
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