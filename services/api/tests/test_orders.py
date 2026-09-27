from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.models.domain import Address, Customer, Order, OrderItem, PaymentAttempt, now
from app.schemas.domain import CheckoutInput, OrderInput, TransitionInput
from app.services import orders


def add_order(db, data, *, number="GG-DIRECT-ORDER", payment_method="COD"):
    order = Order(
        order_number=number,
        customer_id=data["customer"].id,
        customer_phone="+919876543210",
        idempotency_key=number.lower(),
        request_hash="0" * 64,
        fulfilment_type="DELIVERY",
        payment_method=payment_method,
        subtotal=Decimal("100.25"),
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("100.25"),
        address_snapshot={"line1": "Market road"},
    )
    order.items = [
        OrderItem(
            product_id=data["product"].id,
            variant_id=data["variant"].id,
            product_name="Rice",
            variant_name="1 kg",
            quantity=1,
            unit_mrp=Decimal("120.00"),
            unit_selling_price=Decimal("100.25"),
            line_total=Decimal("100.25"),
        )
    ]
    db.add(order)
    db.commit()
    return order


def checkout(data, **changes):
    return CheckoutInput.model_validate(
        {
            "items": [{"variant_id": data["variant"].id, "quantity": 2}],
            "fulfilment_type": "DELIVERY",
            "address_id": data["address"].id,
            "payment_method": "COD",
            **changes,
        }
    )


def test_customer_retrieval_and_reordering_are_customer_scoped(db, data):
    order = add_order(db, data)

    assert orders.list_for_customer(db, data["customer"].id, 1) == [order]
    assert orders.get_for_customer(db, data["customer"].id, order.id) == order
    reordered = orders.reorder(db, data["customer"].id, order.id)
    assert reordered["items"] == [{"variant_id": data["variant"].id, "quantity": 1}]
    assert reordered["products"][0].variants[0].selling_price == Decimal("100.25")

    data["variant"].selling_price = Decimal("90.00")
    db.commit()
    assert orders.reorder(db, data["customer"].id, order.id)["products"][0].variants[
        0
    ].selling_price == Decimal("90.00")
    data["variant"].available = False
    db.commit()
    unavailable = orders.reorder(db, data["customer"].id, order.id)
    assert unavailable["items"] == []
    assert unavailable["unavailable"] == ["Rice · 1 kg"]

    for operation in (
        lambda: orders.get_for_customer(db, 999_999, order.id),
        lambda: orders.reorder(db, 999_999, order.id),
    ):
        with pytest.raises(DomainError) as error:
            operation()
        assert (error.value.code, error.value.status) == ("NOT_FOUND", 404)


def test_owner_retrieval_uses_the_order_lifecycle_interface(db, data):
    placed = add_order(db, data, number="GG-DIRECT-OWNER-PLACED")
    delivered = add_order(db, data, number="GG-DIRECT-OWNER-DELIVERED")
    delivered.status = "DELIVERED"
    db.commit()

    assert orders.list_for_owner(db, 1, "PLACED") == [placed]
    assert orders.get_for_owner(db, delivered.id) == delivered
    with pytest.raises(DomainError) as error:
        orders.get_for_owner(db, 999_999)
    assert (error.value.code, error.value.status) == ("NOT_FOUND", 404)


def test_quote_and_placement_preserve_snapshots_idempotency_and_lock_revalidation(db, data):
    request = checkout(data)
    quote = orders.quote(db, data["customer"], request)
    placement = OrderInput(
        **request.model_dump(),
        quote_token=quote["quote_token"],
        idempotency_key="direct-stable-request-key",
    )

    first = orders.place_order(db, data["customer"], placement)
    repeated = orders.place_order(db, data["customer"], placement)
    assert repeated.id == first.id
    assert first.total == Decimal("200.50")
    assert first.items[0].product_name == "Rice"
    assert first.address_snapshot["line1"] == "Market road"

    data["variant"].selling_price = Decimal("110.00")
    data["product"].name = "Renamed rice"
    db.commit()
    stale = placement.model_copy(update={"idempotency_key": "direct-stale-request-key"})
    with pytest.raises(DomainError) as error:
        orders.place_order(db, data["customer"], stale)
    assert (error.value.code, error.value.status) == ("STALE_CHECKOUT", 409)
    assert first.items[0].product_name == "Rice"


def test_order_intake_owns_address_scope_and_first_release_restrictions(db, data):
    other_customer = db.scalar(select(Customer).where(Customer.id != data["customer"].id))
    other_address = Address(
        customer_id=other_customer.id,
        recipient_name="Other",
        phone="+919999999999",
        line1="Other road",
        city="Town",
        state="Karnataka",
    )
    db.add(other_address)
    db.commit()
    for request, code in (
        (checkout(data, address_id=other_address.id), "NOT_FOUND"),
        (checkout(data, fulfilment_type="PICKUP", address_id=None), "FULFILMENT_UNAVAILABLE"),
        (checkout(data, payment_method="ONLINE_UPI"), "PAYMENT_METHOD_UNAVAILABLE"),
    ):
        with pytest.raises(DomainError) as error:
            orders.quote(db, data["customer"], request)
        assert error.value.code == code

    cod_request = checkout(data)
    cod_quote = orders.quote(db, data["customer"], cod_request)
    for changes, code in (
        ({"fulfilment_type": "PICKUP", "address_id": None}, "FULFILMENT_UNAVAILABLE"),
        ({"payment_method": "ONLINE_UPI"}, "PAYMENT_METHOD_UNAVAILABLE"),
    ):
        unavailable = OrderInput.model_validate(
            {
                **cod_request.model_dump(),
                **changes,
                "quote_token": cod_quote["quote_token"],
                "idempotency_key": f"direct-unavailable-{code.lower()}",
            }
        )
        with pytest.raises(DomainError) as error:
            orders.place_order(db, data["customer"], unavailable)
        assert error.value.code == code


@pytest.mark.parametrize(
    "field,model_key,code",
    [
        ("active", "product", "PRODUCT_UNAVAILABLE"),
        ("available", "product", "PRODUCT_UNAVAILABLE"),
        ("active", "variant", "VARIANT_UNAVAILABLE"),
        ("available", "variant", "VARIANT_UNAVAILABLE"),
    ],
)
def test_quote_rejects_inactive_and_unavailable_catalogue_items(db, data, field, model_key, code):
    setattr(data[model_key], field, False)
    db.commit()

    with pytest.raises(DomainError) as error:
        orders.quote(db, data["customer"], checkout(data))

    assert error.value.code == code


def test_placement_rejects_tampered_and_other_customer_quotes(db, data):
    request = checkout(data)
    quote = orders.quote(db, data["customer"], request)
    placement = OrderInput(
        **request.model_dump(),
        quote_token="tampered." + quote["quote_token"],
        idempotency_key="direct-tampered-quote",
    )
    with pytest.raises(DomainError) as error:
        orders.place_order(db, data["customer"], placement)
    assert error.value.code == "STALE_CHECKOUT"

    other_customer = db.scalar(select(Customer).where(Customer.id != data["customer"].id))
    other_address = Address(
        customer_id=other_customer.id,
        recipient_name="Other",
        phone="+919999999999",
        line1="Other road",
        city="Town",
        state="Karnataka",
    )
    db.add(other_address)
    db.commit()
    other_placement = OrderInput(
        **request.model_dump(exclude={"address_id"}),
        address_id=other_address.id,
        quote_token=quote["quote_token"],
        idempotency_key="direct-other-customer-quote",
    )
    with pytest.raises(DomainError) as error:
        orders.place_order(db, other_customer, other_placement)
    assert error.value.code == "STALE_CHECKOUT"


def test_payment_mutations_are_owned_by_the_order_lifecycle(db, data):
    online = add_order(
        db,
        data,
        number="GG-DIRECT-ONLINE",
        payment_method="ONLINE_UPI",
    )
    online.payment_attempts = [
        PaymentAttempt(
            provider="development",
            reference="direct-development-payment",
            amount=Decimal("100.25"),
        )
    ]
    cash = add_order(db, data, number="GG-DIRECT-CASH")
    db.commit()

    paid = orders.complete_development_payment(db, data["customer"].id, online.id, "PAID")
    assert (paid.payment_status, paid.payment_attempts[-1].status) == ("PAID", "PAID")
    assert orders.mark_cash_received(db, cash.id).payment_status == "PAID"

    with pytest.raises(DomainError) as error:
        orders.complete_development_payment(db, 999_999, online.id, "FAILED")
    assert (error.value.code, error.value.status) == ("NOT_FOUND", 404)

    legacy_on_delivery = add_order(
        db,
        data,
        number="GG-DIRECT-UPI-ON-DELIVERY",
        payment_method="UPI_ON_DELIVERY",
    )
    assert orders.mark_cash_received(db, legacy_on_delivery.id).payment_status == "PAID"


def test_terminal_transition_erases_deleted_customer_delivery_details(db, data):
    order = add_order(db, data, number="GG-DIRECT-DELETED")
    order.customer_deleted_at = now()
    db.commit()

    transitioned = orders.transition(
        db,
        order.id,
        TransitionInput(status="CANCELLED", reason="Customer requested cancellation"),
    )

    assert transitioned.status == "CANCELLED"
    assert transitioned.customer_phone is None
    assert transitioned.address_snapshot is None


def test_transitions_preserve_delivery_and_legacy_pickup_rules(db, data):
    delivery = add_order(db, data, number="GG-DIRECT-DELIVERY")
    with pytest.raises(DomainError) as error:
        orders.transition(db, delivery.id, TransitionInput(status="DELIVERED"))
    assert error.value.code == "INVALID_TRANSITION"
    orders.transition(db, delivery.id, TransitionInput(status="ACCEPTED"))
    orders.transition(db, delivery.id, TransitionInput(status="OUT_FOR_DELIVERY"))
    assert orders.transition(db, delivery.id, TransitionInput(status="DELIVERED")).status == (
        "DELIVERED"
    )

    pickup = add_order(db, data, number="GG-DIRECT-PICKUP")
    pickup.fulfilment_type = "PICKUP"
    db.commit()
    orders.transition(db, pickup.id, TransitionInput(status="ACCEPTED"))
    assert orders.transition(db, pickup.id, TransitionInput(status="DELIVERED")).status == (
        "DELIVERED"
    )


def test_transitions_preserve_cancellation_and_online_payment_rules(db, data):
    order = add_order(db, data, number="GG-DIRECT-CANCELLATION")
    with pytest.raises(DomainError) as error:
        orders.transition(db, order.id, TransitionInput(status="CANCELLED"))
    assert error.value.code == "REASON_REQUIRED"
    assert (
        orders.transition(
            db,
            order.id,
            TransitionInput(status="CANCELLED", reason="Cannot serve address"),
        ).status
        == "CANCELLED"
    )

    online = add_order(
        db,
        data,
        number="GG-DIRECT-ONLINE-TRANSITION",
        payment_method="ONLINE_UPI",
    )
    online.payment_attempts = [
        PaymentAttempt(
            provider="development",
            reference="direct-online-transition",
            amount=Decimal("100.25"),
        )
    ]
    db.commit()
    with pytest.raises(DomainError) as error:
        orders.transition(db, online.id, TransitionInput(status="ACCEPTED"))
    assert error.value.code == "PAYMENT_PENDING"
    orders.complete_development_payment(db, data["customer"].id, online.id, "PAID")
    assert orders.transition(db, online.id, TransitionInput(status="ACCEPTED")).status == (
        "ACCEPTED"
    )
    with pytest.raises(DomainError) as error:
        orders.transition(
            db,
            online.id,
            TransitionInput(status="CANCELLED", reason="Cannot fulfil"),
        )
    assert error.value.code == "REFUND_REQUIRED"
