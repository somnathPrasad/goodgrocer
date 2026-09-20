"""Provider boundaries. Production adapters must be explicitly wired here."""

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Protocol
from urllib.parse import quote
from uuid import uuid4

import httpx
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.core.errors import DomainError


class OTPProvider(Protocol):
    def send(self, phone: str, code: str) -> None: ...


class DevelopmentOTPProvider:
    def send(self, phone: str, code: str) -> None:
        # The request response exposes this code only in development.
        if get_settings().environment == "production":
            raise RuntimeError("Development OTP forbidden")


def otp_provider() -> OTPProvider:
    if get_settings().otp_provider == "development" and get_settings().environment != "production":
        return DevelopmentOTPProvider()
    raise DomainError("OTP_NOT_CONFIGURED", "Phone login is not configured", 503)


class PaymentProvider(Protocol):
    name: str

    def create_attempt(self, order_number: str, amount: Decimal, currency: str = "INR") -> str: ...


class DevelopmentPaymentProvider:
    name = "development"

    def create_attempt(self, order_number: str, amount: Decimal, currency: str = "INR") -> str:
        if get_settings().environment == "production":
            raise RuntimeError("Development payments forbidden")
        return "dev_" + uuid4().hex


def payment_provider() -> PaymentProvider:
    if (
        get_settings().payment_provider == "development"
        and get_settings().environment != "production"
    ):
        return DevelopmentPaymentProvider()
    raise DomainError(
        "PAYMENT_NOT_CONFIGURED",
        "Online UPI is not available. Choose payment on delivery.",
        503,
    )


class ImageStorage(Protocol):
    def save(self, content: bytes) -> str: ...


def prepare_image(content: bytes) -> tuple[str, bytes]:
    if len(content) > 5 * 1024 * 1024:
        raise DomainError("IMAGE_TOO_LARGE", "Images must be at most 5 MB", 413)
    try:
        with Image.open(BytesIO(content)) as source:
            if (
                source.format not in {"JPEG", "PNG", "WEBP"}
                or source.width * source.height > 20_000_000
            ):
                raise ValueError()
            source.load()
            source.thumbnail((1800, 1800))
            clean = source.convert("RGB")
            output = BytesIO()
            clean.save(output, format="JPEG", quality=88)
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ):
        raise DomainError(
            "INVALID_IMAGE",
            "Upload a valid JPEG, PNG or WebP image under 20 megapixels",
        ) from None
    return uuid4().hex + ".jpg", output.getvalue()


class LocalImageStorage:
    def __init__(self, directory: Path):
        self.directory = directory

    def save(self, content: bytes) -> str:
        name, clean = prepare_image(content)
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / name).write_bytes(clean)
        return "/media/" + name


class SupabaseImageStorage:
    def __init__(
        self,
        url: str,
        secret_key: str,
        bucket: str,
        client: httpx.Client | None = None,
    ):
        self.url = url.rstrip("/")
        self.secret_key = secret_key
        self.bucket = bucket
        self.client = client

    def _upload(self, client: httpx.Client, path: str, content: bytes) -> None:
        encoded_bucket = quote(self.bucket, safe="")
        encoded_path = quote(path, safe="/")
        response = client.post(
            f"{self.url}/storage/v1/object/{encoded_bucket}/{encoded_path}",
            headers={
                "apikey": self.secret_key,
                "Content-Type": "image/jpeg",
                "cache-control": "31536000",
                "x-upsert": "false",
            },
            content=content,
        )
        response.raise_for_status()

    def save(self, content: bytes) -> str:
        name, clean = prepare_image(content)
        path = "catalogue/" + name
        encoded_bucket = quote(self.bucket, safe="")
        encoded_path = quote(path, safe="/")
        try:
            if self.client is not None:
                self._upload(self.client, path, clean)
            else:
                with httpx.Client(timeout=10) as client:
                    self._upload(client, path, clean)
        except httpx.HTTPError:
            raise DomainError(
                "IMAGE_STORAGE_UNAVAILABLE",
                "Image storage is temporarily unavailable. Try again.",
                503,
            ) from None
        return f"{self.url}/storage/v1/object/public/{encoded_bucket}/{encoded_path}"


def image_storage() -> ImageStorage:
    settings = get_settings()
    if settings.image_storage_provider == "supabase":
        return SupabaseImageStorage(
            str(settings.supabase_url),
            settings.supabase_secret_key.get_secret_value(),
            settings.supabase_storage_bucket,
        )
    return LocalImageStorage(settings.media_dir)
