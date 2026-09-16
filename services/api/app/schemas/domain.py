import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Money = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Name = Annotated[str, Field(min_length=1, max_length=120)]
Slug = Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=160)]


def normalize_phone(value: str) -> str:
    value = re.sub(r"[\s()-]", "", value)
    if re.fullmatch(r"[6-9]\d{9}", value):
        value = "+91" + value
    if not re.fullmatch(r"\+[1-9]\d{7,14}", value):
        raise ValueError("Use an international phone number, for example +919876543210")
    return value


def validate_image_url(value: str | None) -> str | None:
    if value and not (value.startswith("/media/") or value.startswith("https://")):
        raise ValueError("Use an uploaded media path or HTTPS image URL")
    return value


class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")


class BrandInput(Schema):
    name: Name
    slug: Slug
    active: bool = True


class BrandOut(BrandInput):
    id: int


class CategoryInput(BrandInput):
    image_url: str | None = Field(default=None, max_length=500)
    display_order: int = 0

    @field_validator("image_url")
    @classmethod
    def image_safe(cls, value):
        return validate_image_url(value)


class CategoryOut(CategoryInput):
    id: int


class VariantInput(Schema):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    mrp: Money
    selling_price: Money
    active: bool = True
    available: bool = True
    display_order: int = 0

    @model_validator(mode="after")
    def prices(self):
        if self.selling_price > self.mrp:
            raise ValueError("Selling price cannot exceed MRP")
        return self


class VariantOut(VariantInput):
    id: int
    product_id: int


class ProductInput(BrandInput):
    image_url: str | None = Field(default=None, max_length=500)
    brand_id: int
    description: str = Field(default="", max_length=10000)
    available: bool = True
    category_ids: list[int] = Field(default_factory=list, max_length=100)

    @field_validator("image_url")
    @classmethod
    def image_safe(cls, value):
        return validate_image_url(value)


class ProductOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    image_url: str | None
    active: bool
    available: bool
    brand_id: int
    brand: BrandOut
    categories: list[CategoryOut]
    variants: list[VariantOut]


class ProductPage(Schema):
    items: list[ProductOut]
    total: int
    page: int
    page_size: int


class PhoneInput(Schema):
    phone_number: str
    _phone = field_validator("phone_number")(normalize_phone)


class VerifyInput(PhoneInput):
    code: str = Field(pattern=r"^\d{6}$")


class OTPResponse(Schema):
    message: str
    development_code: str | None = None


class TokenResponse(Schema):
    token: str
    expires_at: datetime


class LoginInput(Schema):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class AddressInput(Schema):
    recipient_name: Name
    phone: str
    line1: str = Field(min_length=1, max_length=250)
    line2: str | None = Field(default=None, max_length=250)
    landmark: str | None = Field(default=None, max_length=250)
    locality: str | None = Field(default=None, max_length=150)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, max_length=12)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    _phone = field_validator("phone")(normalize_phone)


class AddressOut(AddressInput):
    id: int


class CartItem(Schema):
    variant_id: int
    quantity: int = Field(gt=0, le=99)


class CheckoutInput(Schema):
    items: list[CartItem] = Field(min_length=1, max_length=100)
    fulfilment_type: Literal["DELIVERY", "PICKUP"]
    address_id: int | None = None
    payment_method: Literal["COD", "UPI_ON_DELIVERY", "ONLINE_UPI"]

    @model_validator(mode="after")
    def valid_cart(self):
        if len({i.variant_id for i in self.items}) != len(self.items):
            raise ValueError("Duplicate variants in cart")
        if self.fulfilment_type == "DELIVERY" and self.address_id is None:
            raise ValueError("Choose a delivery address")
        return self


class OrderInput(CheckoutInput):
    quote_token: str
    idempotency_key: str = Field(min_length=16, max_length=80)


class ItemOut(Schema):
    product_id: int
    variant_id: int
    product_name: str
    variant_name: str
    quantity: int
    unit_mrp: Decimal
    unit_selling_price: Decimal
    line_total: Decimal


class QuoteOut(Schema):
    items: list[ItemOut]
    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    total: Decimal
    address_snapshot: dict | None
    quote_token: str
    expires_in: int = 600


class PaymentOut(Schema):
    id: int
    provider: str
    reference: str
    status: str
    amount: Decimal


class OrderOut(Schema):
    id: int
    order_number: str
    customer_phone: str
    fulfilment_type: str
    status: str
    payment_method: str
    payment_status: str
    subtotal: Decimal
    delivery_fee: Decimal
    discount: Decimal
    total: Decimal
    address_snapshot: dict | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
    items: list[ItemOut]
    payment_attempts: list[PaymentOut]


class TransitionInput(Schema):
    status: Literal["ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    reason: str | None = Field(default=None, max_length=500)


class ReorderOut(Schema):
    items: list[CartItem]
    products: list[ProductOut]
    unavailable: list[str]
