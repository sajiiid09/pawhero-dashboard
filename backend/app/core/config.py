from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pfoten-Held API"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/pawhero",
        validation_alias=AliasChoices("DATABASE_URL"),
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        validation_alias=AliasChoices("CORS_ORIGINS"),
    )
    demo_owner_id: str = "owner-demo"
    jwt_secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("JWT_SECRET_KEY"),
    )
    jwt_access_token_expire_minutes: int = 60

    smtp_host: str = Field(default="localhost", validation_alias=AliasChoices("SMTP_HOST"))
    smtp_port: int = Field(default=587, validation_alias=AliasChoices("SMTP_PORT"))
    smtp_user: str = Field(default="", validation_alias=AliasChoices("SMTP_USER"))
    smtp_password: str = Field(default="", validation_alias=AliasChoices("SMTP_PASSWORD"))
    smtp_from: str = Field(
        default="Pfoten-Held <noreply@localhost>",
        validation_alias=AliasChoices("SMTP_FROM"),
    )
    app_url: str = Field(default="http://localhost:3000", validation_alias=AliasChoices("APP_URL"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
