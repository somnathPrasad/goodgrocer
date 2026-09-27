"""Transaction map and atomicity tests.

FastAPI requests own the transaction around module calls. Modules flush their
workflow changes without committing, and CLI callers commit their completed
commands. Rate-limit accounting is the intentional exception: it is committed
before authentication so rejected attempts remain durable.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import Settings
from app.core.errors import DomainError
from app.main import app
from app.models.domain import Address, AuthSession, Customer, Order, RateLimit, now
from app.schemas.domain import CheckoutInput, OrderInput
from app.services import auth, customer_deletion, orders


class FailingCommitDatabase:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def scalars(self, statement):
        return self

    def all(self):
        return []

    def get(self, model, object_id):
        if model is AuthSession:
            return AuthSession(
                token_hash=object_id,
                customer_id=1,
                expires_at=now() + timedelta(minutes=5),
            )
        if model is Customer:
            return Customer(id=1)
        raise AssertionError(f"Unexpected model lookup: {model}")

    def delete(self, value):
        self.events.append("delete")

    def flush(self):
        self.events.append("flush")

    def commit(self):
        self.events.append("commit")
        raise RuntimeError("database commit failed")

    def rollback(self):
        self.events.append("rollback")


def test_commit_failure_is_handled_before_a_success_response(monkeypatch):
    events = []
    database = FailingCommitDatabase(events)
    monkeypatch.setattr("app.api.dependencies.SessionLocal", lambda: database)

    async def recording_app(scope, receive, send):
        async def record_send(message):
            if message["type"] == "http.response.start":
                events.append(f"response-start:{message['status']}")
            elif message["type"] == "http.response.body" and not message.get("more_body"):
                events.append("response-finished")
            await send(message)

        await app(scope, receive, record_send)

    app.dependency_overrides.pop(get_db, None)
    with TestClient(recording_app, raise_server_exceptions=False) as test_client:
        response = test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer customer-session"},
        )

    assert events == [
        "delete",
        "flush",
        "commit",
        "rollback",
        "response-start:500",
        "response-finished",
    ]
    assert response.status_code == 500


def checkout(data):
    return CheckoutInput.model_validate(
        {
            "items": [{"variant_id": data["variant"].id, "quantity": 1}],
            "fulfilment_type": "DELIVERY",
            "address_id": data["address"].id,
            "payment_method": "COD",
        }
    )


def configure_google(monkeypatch, subject):
    monkeypatch.setattr(
        "app.services.auth.get_settings",
        lambda: Settings(google_web_client_id="web-client.apps.googleusercontent.com"),
    )

    def verify(token, request, audience):
        if token == "invalid":
            raise ValueError("bad signature")
        return {"sub": subject}

    monkeypatch.setattr("app.services.auth.google_id_token.verify_oauth2_token", verify)


def test_order_placement_flushes_until_the_request_owner_commits(db, data):
    request = checkout(data)
    quoted = orders.quote(db, data["customer"], request)
    placement = OrderInput(
        **request.model_dump(),
        quote_token=quoted["quote_token"],
        idempotency_key="transaction-owner-order",
    )

    placed = orders.place_order(db, data["customer"], placement)

    with Session(db.bind) as observer:
        assert observer.get(Order, placed.id) is None
    db.rollback()
    with Session(db.bind) as observer:
        assert observer.get(Order, placed.id) is None

    quoted = orders.quote(db, data["customer"], request)
    placed = orders.place_order(
        db,
        data["customer"],
        placement.model_copy(update={"quote_token": quoted["quote_token"]}),
    )
    db.commit()
    with Session(db.bind) as observer:
        assert observer.get(Order, placed.id) is not None


def test_rejected_sign_in_keeps_rate_limit_but_success_waits_for_request_commit(db, monkeypatch):
    configure_google(monkeypatch, "transaction-google-subject")

    with pytest.raises(DomainError) as error:
        auth.google_login(db, "invalid", "192.0.2.10")
    assert error.value.code == "INVALID_GOOGLE_TOKEN"

    rate_key = "google-ip:" + auth.digest("192.0.2.10")
    with Session(db.bind) as observer:
        assert observer.get(RateLimit, rate_key).count == 1

    session = auth.google_login(db, "valid", "192.0.2.10")
    with Session(db.bind) as observer:
        assert (
            observer.query(Customer)
            .filter_by(google_subject="transaction-google-subject")
            .one_or_none()
            is None
        )
        assert observer.get(AuthSession, auth.digest(session["token"])) is None

    db.commit()
    with Session(db.bind) as observer:
        customer = (
            observer.query(Customer).filter_by(google_subject="transaction-google-subject").one()
        )
        assert observer.get(AuthSession, auth.digest(session["token"])).customer_id == customer.id


def test_customer_deletion_rolls_back_or_commits_as_one_workflow(db, data, monkeypatch):
    subject = "transaction-deletion-subject"
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
    retained = Order(
        order_number="GG-TRANSACTION-DELETE",
        customer_id=customer.id,
        customer_phone="+919999999999",
        idempotency_key="transaction-delete-order",
        request_hash="1" * 64,
        fulfilment_type="DELIVERY",
        payment_method="COD",
        subtotal=Decimal("100.25"),
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("100.25"),
        address_snapshot={"line1": "Private road"},
    )
    db.add_all([address, retained])
    db.commit()
    customer_id, address_id, order_id = customer.id, address.id, retained.id

    with pytest.raises(DomainError) as error:
        customer_deletion.delete_customer(
            db,
            "valid",
            "192.0.2.20",
            current_customer_id=data["customer"].id,
        )
    assert error.value.code == "GOOGLE_ACCOUNT_MISMATCH"
    ip_rate_key = "customer-delete-ip:" + auth.digest("192.0.2.20")
    subject_rate_key = "customer-delete-subject:" + auth.digest(subject)
    with Session(db.bind) as observer:
        assert observer.get(RateLimit, ip_rate_key).count == 1
        assert observer.get(RateLimit, subject_rate_key).count == 1

    customer_deletion.delete_customer(db, "valid", "192.0.2.20")
    db.rollback()
    assert db.get(Customer, customer_id) is not None
    assert db.get(Address, address_id) is not None
    assert db.get(Order, order_id).customer_id == customer_id

    customer_deletion.delete_customer(db, "valid", "192.0.2.20")
    db.commit()
    with Session(db.bind) as observer:
        assert observer.get(Customer, customer_id) is None
        assert observer.get(Address, address_id) is None
        order = observer.get(Order, order_id)
        assert order.customer_id is None
        assert order.customer_deleted_at is not None
