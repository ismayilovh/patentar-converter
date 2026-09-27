from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_publishable_key: str = ""
    public_base_url: str = ""
    cors_origins: str = "*"
    supabase_timeout_seconds: float = 10.0

    @property
    def supabase_is_configured(self) -> bool:
        return bool(self.supabase_url.strip() and self.supabase_publishable_key.strip())

    @cached_property
    def parsed_cors_origins(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        return origins or ["*"]

    @property
    def normalized_public_base_url(self) -> str:
        return self.public_base_url.strip().rstrip("/")
