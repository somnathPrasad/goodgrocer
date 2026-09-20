from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE, env_file_encoding="utf-8", extra="ignore"
    )
    database_url: PostgresDsn
    environment: Literal["development", "test", "production"] = "development"
    secret_key: str = "local-development-only-change-before-production"
    otp_provider: Literal["development", "disabled"] = "development"
    payment_provider: Literal["development", "disabled"] = "development"
    image_storage_provider: Literal["local", "supabase"] = "local"
    media_dir: Path = Path(__file__).resolve().parents[2] / "media"
    supabase_url: HttpUrl | None = None
    supabase_secret_key: SecretStr | None = None
    supabase_storage_bucket: str = Field(
        default="catalogue-images",
        min_length=1,
        max_length=100,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
    )
    public_api_url: str = "http://localhost:8000"
    admin_origin: str = "http://localhost:3000"
    delivery_fee: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    session_hours: int = Field(default=168, gt=0, le=720)

    @model_validator(mode="after")
    def production_safe(self):
        if self.delivery_fee < 0:
            raise ValueError("Delivery fee must be nonnegative")
        if self.image_storage_provider == "supabase":
            if self.supabase_url is None or self.supabase_url.scheme != "https":
                raise ValueError("Supabase image storage requires an HTTPS SUPABASE_URL")
            if (
                self.supabase_secret_key is None
                or not self.supabase_secret_key.get_secret_value().startswith("sb_secret_")
            ):
                raise ValueError("Supabase image storage requires a current SUPABASE_SECRET_KEY")
        if self.environment == "production":
            if self.image_storage_provider != "supabase":
                raise ValueError("Production requires Supabase image storage")
            if self.otp_provider == "development" or self.payment_provider == "development":
                raise ValueError("Development providers are forbidden in production")
            if len(self.secret_key) < 32 or self.secret_key.startswith("local-development"):
                raise ValueError("Set a random production SECRET_KEY of at least 32 characters")
            if not self.admin_origin.startswith("https://") or not self.public_api_url.startswith(
                "https://"
            ):
                raise ValueError("Production URLs require HTTPS")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
