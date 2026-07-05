from functools import lru_cache

from pydantic import computed_field
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
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

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

    @computed_field
    @property
    def database_url(self) -> str:
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