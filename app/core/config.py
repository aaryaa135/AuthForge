from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    # =========================
    # Application
    # =========================
    app_name: str
    app_version: str
    environment: str
    debug: bool

    # =========================
    # API
    # =========================
    api_host: str
    api_port: int

    # =========================
    # Database
    # =========================
    database_url: str | None = None

    db_host: str | None = None
    db_port: int | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None

    # =========================
    # JWT
    # =========================
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int

    # =========================
    # Logging
    # =========================
    log_level: str

    # =========================
    # Redis
    # =========================

    redis_host: str
    redis_port: int
    redis_db: int
    redis_password: str | None = None

    # =========================
    # Frontend / Links
    # =========================
    frontend_url: str = "http://localhost:8000"
    require_email_verification: bool = False
    cors_origins: str = ""  # comma-separated, e.g. "https://app.example.com,https://admin.example.com"

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        if v in ("<LONG_RANDOM_SECRET>", "change-me", "secret"):
            raise ValueError("JWT_SECRET_KEY is placeholder — set a strong random value")
        return v

    @field_validator("environment")
    @classmethod
    def validate_env(cls, v: str) -> str:
        if v not in ("development", "test", "staging", "production"):
            raise ValueError("ENVIRONMENT must be one of development/test/staging/production")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip():
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.environment == "production":
            return [self.frontend_url]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url:
            return self.database_url

        if not all(
            [
                self.db_host,
                self.db_port,
                self.db_name,
                self.db_user,
                self.db_password,
            ]
        ):
            raise ValueError(
                "Either DATABASE_URL or all DB_* variables must be provided."
            )

        return (
            f"postgresql+psycopg2://"
            f"{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}"
            f"/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}"
                f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
            )

        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
