from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
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
        default="change-me-in-production-with-32-byte-minimum",
        validation_alias=AliasChoices("JWT_SECRET_KEY"),
    )
    jwt_access_token_expire_minutes: int = 60
    email_verification_ttl_minutes: int = Field(
        default=10,
        validation_alias=AliasChoices("EMAIL_VERIFICATION_TTL_MINUTES"),
    )
    email_verification_resend_cooldown_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices("EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS"),
    )

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

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError(
                "JWT_SECRET_KEY muss mindestens 32 Byte lang sein (RFC 7518, HS256)."
            )
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
