from datetime import timedelta
from decimal import Decimal

from app.core.config import Settings
from app.models.domain import Address, AuthSession, Customer, Favourite, Order, PaymentAttempt
from app.services import customer_deletion
from app.services.auth import new_session


def configure_google(monkeypatch, subject):
    monkeypatch.setattr(
        "app.services.auth.get_settings",
        lambda: Settings(google_web_client_id="web-client.apps.googleusercontent.com"),
    )
    monkeypatch.setattr(
        "app.services.auth.google_id_token.verify_oauth2_token",
        lambda token, request, audience: {"sub": subject, "email": "delete@example.com"},
    )


def retained_order(customer, number, status="PLACED"):
    return Order(
        order_number=number,
        customer_id=customer.id,
        customer_phone="+919999999999",
        idempotency_key=number.lower(),
        request_hash="1" * 64,
        fulfilment_type="DELIVERY",
        status=status,
        payment_method="COD",
        subtotal=Decimal("100.25"),
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("100.25"),
        address_snapshot={
            "recipient_name": "Delete Me",
            "phone": "+919999999999",
            "line1": "Private road",
            "city": "Town",
            "state": "Karnataka",
        },
    )


def test_customer_deletion_removes_reusable_data_and_retains_only_required_order_data(
    db,
    data,
    monkeypatch,
):
    subject = "delete-google-subject"
    configure_google(monkeypatch, subject)
    customer = Customer(google_subject=subject)
    db.add(customer)
    db.flush()
    address = Address(
        customer_id=customer.id,
        recipient_name="Delete Me",
        phone="+919999999999",
        line1="Private road",
        city="Town",
        state="Karnataka",
    )
    active = retained_order(customer, "GG-DELETE-ACTIVE")
    expiring = retained_order(customer, "GG-DELETE-EXPIRING")
    terminal = retained_order(customer, "GG-DELETE-TERMINAL", "DELIVERED")
    db.add_all(
        [
            address,
            Favourite(customer_id=customer.id, product_id=data["product"].id),
            active,
            expiring,
            terminal,
        ]
    )
    db.flush()
    db.add(
        PaymentAttempt(
            order_id=active.id,
            provider="development",
            reference="delete-this-attempt",
            amount=Decimal("100.25"),
        )
    )
    new_session(db, customer_id=customer.id)
    db.commit()

    customer_deletion.delete_customer(
        db,
        "fresh-delete-token",
        "192.0.2.30",
        current_customer_id=customer.id,
    )

    assert db.get(Customer, customer.id) is None
    assert db.query(Address).filter_by(customer_id=customer.id).count() == 0
    assert db.query(Favourite).filter_by(customer_id=customer.id).count() == 0
    assert db.query(AuthSession).filter_by(customer_id=customer.id).count() == 0
    assert db.query(PaymentAttempt).filter_by(order_id=active.id).count() == 0
    active = db.get(Order, active.id)
    terminal = db.get(Order, terminal.id)
    assert active.customer_id is None and active.customer_deleted_at is not None
    assert active.customer_phone == "+919999999999" and active.address_snapshot is not None
    assert active.delivery_details_erase_at - active.customer_deleted_at == timedelta(days=30)
    assert terminal.customer_id is None and terminal.customer_phone is None
    assert terminal.address_snapshot is None

    assert (
        customer_deletion.erase_expired_delivery_details(
            db,
            expiring.delivery_details_erase_at,
        )
        == 2
    )
    db.refresh(active)
    db.refresh(expiring)
    assert active.customer_phone is None and active.address_snapshot is None
    assert expiring.customer_phone is None and expiring.address_snapshot is None

    customer_deletion.delete_customer(db, "fresh-delete-token", "192.0.2.30")
