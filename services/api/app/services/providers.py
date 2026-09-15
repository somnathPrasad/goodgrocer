"""Provider boundaries. Production adapters must be explicitly wired here."""

from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Protocol
from uuid import uuid4

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


class LocalImageStorage:
    def __init__(self, directory: Path):
        self.directory = directory

    def save(self, content: bytes) -> str:
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
                name = uuid4().hex + ".jpg"
                self.directory.mkdir(parents=True, exist_ok=True)
                clean.save(self.directory / name, format="JPEG", quality=88)
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
        return "/media/" + name


def image_storage() -> ImageStorage:
    return LocalImageStorage(get_settings().media_dir)
