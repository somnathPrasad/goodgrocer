import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_production_rejects_development_providers():
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_supabase_storage_requires_current_backend_credentials():
    with pytest.raises(ValidationError, match="HTTPS SUPABASE_URL"):
        Settings(image_storage_provider="supabase", supabase_url=None, supabase_secret_key=None)
    with pytest.raises(ValidationError, match="current SUPABASE_SECRET_KEY"):
        Settings(
            image_storage_provider="supabase",
            supabase_url="https://example.supabase.co",
            supabase_secret_key="legacy-key",
        )


def test_production_accepts_supabase_storage_configuration():
    settings = Settings(
        environment="production",
        google_web_client_id="web-client.apps.googleusercontent.com",
        payment_provider="disabled",
        secret_key="a-production-secret-that-is-long-enough",
        public_api_url="https://api.example.com",
        admin_origin="https://admin.example.com",
        image_storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_secret_key="sb_secret_test",
    )

    assert settings.image_storage_provider == "supabase"
