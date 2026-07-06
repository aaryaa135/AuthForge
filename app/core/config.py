from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


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
    database_url: Optional[str] = None

    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
