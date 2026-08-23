from uuid import UUID

from app.core.logger import logger
from app.modules.roles.repository import RoleRepository
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


class UserService:

    """
    Handles user-related business logic.
    """

    def __init__(
        self,
        repository: UserRepository,
    ):
        self.repository = repository

    def list_users(self) -> list[UserResponse]:
        users = self.repository.get_all()

        return [
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

    def update_role(
        self,
        user_id: UUID,
        role_name: str,
        role_repository: RoleRepository,
    ) -> UserResponse:
        """
        Update a user's role.
        """

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        role = role_repository.get_by_name(role_name)

        if role is None:
            raise ValueError("Role not found.")

        user.role_id = role.id

        user = self.repository.update(user)

        logger.info(
            "Role updated: %s -> %s",
            user.email,
            role.name,
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

    def get_user(
        self,
        user_id: UUID,
    ) -> UserResponse:
        """
        Get a single user by ID.
        """

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )

    def update_status(
        self,
        user_id: UUID,
        is_active: bool,
    ) -> UserResponse:
        """
        Activate or deactivate a user.
        """

        user = self.repository.get_by_id(user_id)

        if user is None:
            raise ValueError("User not found.")

        user.is_active = is_active

        user = self.repository.update(user)

        logger.info(
            "User status updated: %s -> active=%s",
            user.email,
            user.is_active,
        )

        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role.name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
        )
