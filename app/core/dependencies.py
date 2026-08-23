from fastapi import Depends, HTTPException, status

from app.modules.users.models import User
from app.shared.dependencies import get_current_user


def require_role(*roles: str):
    """
    Allow access if the current user has one of the allowed roles.
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned role.",
            )

        if current_user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker
