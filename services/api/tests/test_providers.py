from io import BytesIO

import httpx
import pytest
from PIL import Image

from app.core.config import Settings
from app.core.errors import DomainError
from app.services import providers
from app.services.providers import SupabaseImageStorage


def png() -> bytes:
    content = BytesIO()
    Image.new("RGBA", (10, 10), (255, 0, 0, 128)).save(content, format="PNG")
    return content.getvalue()


def test_supabase_storage_uploads_clean_jpeg_and_returns_public_url():
    def upload(request: httpx.Request):
        assert request.url.path.startswith("/storage/v1/object/catalogue-images/catalogue/")
        assert request.url.path.endswith(".jpg")
        assert request.headers["apikey"] == "sb_secret_test"
        assert request.headers["content-type"] == "image/jpeg"
        assert request.headers["x-upsert"] == "false"
        with Image.open(BytesIO(request.content)) as uploaded:
            assert uploaded.format == "JPEG"
            assert uploaded.mode == "RGB"
        return httpx.Response(200, json={"Key": request.url.path})

    storage = SupabaseImageStorage(
        "https://example.supabase.co",
        "sb_secret_test",
        "catalogue-images",
        httpx.Client(transport=httpx.MockTransport(upload)),
    )

    url = storage.save(png())

    assert url.startswith(
        "https://example.supabase.co/storage/v1/object/public/catalogue-images/catalogue/"
    )
    assert url.endswith(".jpg")


@pytest.mark.parametrize("status", [401, 404, 500])
def test_supabase_storage_hides_upstream_failures(status):
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status, json={"message": "private upstream detail"})
        )
    )
    storage = SupabaseImageStorage(
        "https://example.supabase.co",
        "sb_secret_test",
        "catalogue-images",
        client,
    )

    with pytest.raises(DomainError) as error:
        storage.save(png())

    assert error.value.code == "IMAGE_STORAGE_UNAVAILABLE"
    assert error.value.status == 503
    assert "private upstream detail" not in error.value.message


def test_store_catalogue_image_validates_type_and_uses_configured_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(
        providers,
        "get_settings",
        lambda: Settings(media_dir=tmp_path),
    )

    image_url = providers.store_catalogue_image("image/png", png())

    assert image_url.startswith("/media/")
    assert (tmp_path / image_url.removeprefix("/media/")).is_file()

    with pytest.raises(DomainError) as error:
        providers.store_catalogue_image("text/plain", b"not an image")
    assert error.value.code == "INVALID_IMAGE"
