import hashlib
import json
from decimal import Decimal
from uuid import uuid4

from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import owned
from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.domain import (
    Address,
    Order,
    OrderItem,
    PaymentAttempt,
    Product,
    ProductVariant,
)
from app.schemas.domain import AddressInput, CheckoutInput, ItemOut
from app.services.catalogue import product_out
from app.services.providers import payment_provider


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def signer():
    return URLSafeTimedSerializer(get_settings().secret_key, salt="checkout-v1")


def resolve(db, customer, data, lock=False):
    if data.fulfilment_type != "DELIVERY":
        raise DomainError(
            "FULFILMENT_UNAVAILABLE",
            "Store pickup is not available for this release.",
            422,
        )
    if data.payment_method != "COD":
        raise DomainError(
            "PAYMENT_METHOD_UNAVAILABLE",
            "Only cash payment is available for this release.",
            422,
        )
    if data.payment_method == "ONLINE_UPI":
        payment_provider()
    snapshot = None
    if data.fulfilment_type == "DELIVERY":
        address = owned(db, Address, data.address_id, customer.id)
        snapshot = AddressInput.model_validate(address).model_dump(mode="json")
    elif not (data.contact_phone or customer.phone_number):
        raise DomainError("CONTACT_PHONE_REQUIRED", "Enter a contact phone for pickup", 422)
    ids = sorted(i.variant_id for i in data.items)
    query = (
        select(ProductVariant)
        .options(selectinload(ProductVariant.product))
        .where(ProductVariant.id.in_(ids))
        .order_by(ProductVariant.id)
    )
    if lock:
        # Lock product flags as well as variants; admin updates wait until creation commits.
        product_ids = select(ProductVariant.product_id).where(ProductVariant.id.in_(ids))
        db.scalars(
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        ).all()
        query = query.with_for_update().execution_options(populate_existing=True)
    variants = {v.id: v for v in db.scalars(query).all()}
    lines = []
    for item in data.items:
        variant = variants.get(item.variant_id)
        if variant is None or not variant.active or not variant.available:
            raise DomainError(
                "VARIANT_UNAVAILABLE",
                "A selected variant is no longer available. Update your cart.",
                409,
            )
        product = variant.product
        if not product.active or not product.available:
            raise DomainError("PRODUCT_UNAVAILABLE", f"{product.name} is no longer available", 409)
        lines.append(
            ItemOut(
                product_id=product.id,
                variant_id=variant.id,
                product_name=product.name,
                variant_name=variant.name,
                quantity=item.quantity,
                unit_mrp=variant.mrp,
                unit_selling_price=variant.selling_price,
                line_total=variant.selling_price * item.quantity,
            )
        )
    subtotal = sum((i.line_total for i in lines), Decimal("0.00"))
    fee = get_settings().delivery_fee if data.fulfilment_type == "DELIVERY" else Decimal("0.00")
    if subtotal + fee > Decimal("9999999999.99"):
        raise DomainError("TOTAL_TOO_LARGE", "This basket exceeds the maximum order total")
    return {
        "items": [i.model_dump(mode="json") for i in lines],
        "subtotal": str(subtotal),
        "delivery_fee": str(fee),
        "discount": "0.00",
        "total": str(subtotal + fee),
        "address_snapshot": snapshot,
    }


def checkout_data(data):
    return CheckoutInput.model_validate(
        data.model_dump(include=set(CheckoutInput.model_fields))
    ).model_dump(mode="json")


def quote(db, customer, data):
    result = resolve(db, customer, data)
    result["quote_token"] = signer().dumps(
        {
            "customer": customer.id,
            "request": fingerprint(checkout_data(data)),
            "result": fingerprint(result),
        }
    )
    return result


def place_order(db, customer, data):
    request_hash = fingerprint(checkout_data(data))
    # Serialize per-customer order submissions, including idempotent retries.
    from app.models.domain import Customer

    db.scalar(select(Customer).where(Customer.id == customer.id).with_for_update())
    existing = db.scalar(
        select(Order).where(
            Order.customer_id == customer.id,
            Order.idempotency_key == data.idempotency_key,
        )
    )
    if existing:
        if existing.request_hash != request_hash:
            raise DomainError(
                "IDEMPOTENCY_CONFLICT",
                "This request key was used for another order",
                409,
            )
        return existing
    try:
        signed = signer().loads(data.quote_token, max_age=600)
    except BadSignature:
        raise DomainError(
            "STALE_CHECKOUT", "Checkout expired. Review a fresh total.", 409
        ) from None
    result = resolve(db, customer, data, lock=True)
    if signed != {
        "customer": customer.id,
        "request": request_hash,
        "result": fingerprint(result),
    }:
        raise DomainError(
            "STALE_CHECKOUT",
            "Prices or checkout details changed. Review the new total.",
            409,
        )
    order = Order(
        order_number="GG-" + uuid4().hex[:12].upper(),
        customer_id=customer.id,
        customer_phone=(
            result["address_snapshot"]["phone"]
            if data.fulfilment_type == "DELIVERY"
            else data.contact_phone or customer.phone_number
        ),
        idempotency_key=data.idempotency_key,
        request_hash=request_hash,
        fulfilment_type=data.fulfilment_type,
        payment_method=data.payment_method,
        **{k: v for k, v in result.items() if k != "items"},
    )
    order.items = [OrderItem(**line) for line in result["items"]]
    db.add(order)
    db.flush()
    if data.payment_method == "ONLINE_UPI":
        provider = payment_provider()
        db.add(
            PaymentAttempt(
                order_id=order.id,
                provider=provider.name,
                reference=provider.create_attempt(order.order_number, Decimal(order.total)),
                amount=order.total,
            )
        )
    db.commit()
    db.refresh(order)
    return order


TRANSITIONS = {
    "PLACED": {"ACCEPTED", "CANCELLED"},
    "ACCEPTED": {"OUT_FOR_DELIVERY", "CANCELLED"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "CANCELLED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


def transition(db, order_id, data):
    order = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if order is None:
        raise DomainError("NOT_FOUND", "Order not found", 404)
    allowed = set(TRANSITIONS[order.status])
    if order.fulfilment_type == "PICKUP" and order.status == "ACCEPTED":
        allowed = {"DELIVERED", "CANCELLED"}
    if data.status not in allowed:
        raise DomainError("INVALID_TRANSITION", f"Cannot move {order.status} to {data.status}", 409)
    if (
        data.status == "ACCEPTED"
        and order.payment_method == "ONLINE_UPI"
        and order.payment_status != "PAID"
    ):
        raise DomainError(
            "PAYMENT_PENDING", "Online payment must be completed before accepting", 409
        )
    if data.status == "CANCELLED":
        if not data.reason:
            raise DomainError("REASON_REQUIRED", "Enter a cancellation reason")
        if order.payment_method == "ONLINE_UPI" and order.payment_status == "PAID":
            raise DomainError(
                "REFUND_REQUIRED",
                "Paid online orders require a refund integration before cancellation",
                409,
            )
        order.cancellation_reason = data.reason
    order.status = data.status
    if order.customer_deleted_at is not None and data.status in {"DELIVERED", "CANCELLED"}:
        from app.services.customer_deletion import erase_delivery_details

        erase_delivery_details(order)
    db.commit()
    return order


def reorder(db, order):
    variants = {
        v.id: v
        for v in db.scalars(
            select(ProductVariant)
            .options(selectinload(ProductVariant.product))
            .where(ProductVariant.id.in_([i.variant_id for i in order.items]))
        ).all()
    }
    items, products, unavailable = [], {}, []
    for old in order.items:
        v = variants.get(old.variant_id)
        if v and v.active and v.available and v.product.active and v.product.available:
            items.append({"variant_id": v.id, "quantity": old.quantity})
            products[v.product.id] = product_out(v.product)
        else:
            unavailable.append(f"{old.product_name} · {old.variant_name}")
    return {
        "items": items,
        "products": list(products.values()),
        "unavailable": unavailable,
    }
