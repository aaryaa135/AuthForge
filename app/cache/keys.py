class RedisKeys:
    """
    Centralized Redis key generation.
    """

    @staticmethod
    def user_email(email: str) -> str:
        return f"user:email:{email}"

    @staticmethod
    def user_username(username: str) -> str:
        return f"user:username:{username}"

    @staticmethod
    def blacklist(jti: str) -> str:
        return f"blacklist:{jti}"

    @staticmethod
    def session(user_id: str) -> str:
        return f"session:{user_id}"
