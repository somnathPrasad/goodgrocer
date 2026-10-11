import hashlib
import hmac
import json
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.api.dependencies import get_db
from app.core.config import Settings
from app.main import app
from app.models.domain import WhatsAppWebhookDelivery, now
from app.services import whatsapp_webhooks

PATH = "/api/v1/webhooks/whatsapp"
SECRET = "test-meta-app-secret"
TOKEN = "test-webhook-verify-token"


@pytest.fixture(autouse=True)
def configure_webhook(monkeypatch):
    monkeypatch.setattr(
        whatsapp_webhooks,
        "get_settings",
        lambda: Settings(whatsapp_app_secret=SECRET, whatsapp_webhook_verify_token=TOKEN),
    )


def signed_headers(body):
    signature = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return {"Content-Type": "application/json", "X-Hub-Signature-256": "sha256=" + signature}


def count_deliveries(db):
    return db.scalar(select(func.count()).select_from(WhatsAppWebhookDelivery))


def test_verification_returns_unquoted_challenge(client):
    response = client.get(
        PATH,
        params={"hub.mode": "subscribe", "hub.verify_token": TOKEN, "hub.challenge": "001234"},
    )
    assert response.status_code == 200
    assert response.text == "001234"
    assert response.headers["content-type"].startswith("text/plain")


@pytest.mark.parametrize(
    "params,status",
    [
        ({}, 403),
        ({"hub.mode": "subscribe", "hub.verify_token": "incorrect"}, 403),
        ({"hub.mode": "unsubscribe", "hub.verify_token": TOKEN}, 403),
        ({"hub.mode": "subscribe", "hub.verify_token": TOKEN}, 400),
    ],
)
def test_invalid_verification(client, params, status):
    assert client.get(PATH, params=params).status_code == status


def test_signed_batch_is_durable_and_exact_retries_are_deduplicated(client, db):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messages": [
                                {"id": "message-1", "text": {"body": "hello"}},
                                {"id": "message-2", "text": {"body": "hi"}},
                            ]
                        },
                    }
                ],
            },
            {
                "id": "waba-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "statuses": [
                                {"id": "outbound-1", "status": "delivered"},
                            ]
                        },
                    }
                ],
            },
        ],
    }
    body = json.dumps(payload, indent=2).encode()
    for _ in range(2):
        assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 200
    db.rollback()  # Reading after the request proves it committed rather than merely flushed.
    assert count_deliveries(db) == 1
    row = db.get(WhatsAppWebhookDelivery, hashlib.sha256(body).hexdigest())
    assert row.raw_body == body
    assert json.loads(row.raw_body) == payload


@pytest.mark.parametrize("signature", [None, "bad", "sha256=" + "0" * 64, "sha1=bad"])
def test_unsigned_or_invalid_signatures_are_not_captured(client, db, signature):
    headers = {"Content-Type": "application/json"}
    if signature:
        headers["X-Hub-Signature-256"] = signature
    response = client.post(PATH, content=b"{}", headers=headers)
    assert response.status_code == 403
    assert count_deliveries(db) == 0


def test_signature_is_checked_against_exact_bytes(client, db):
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    response = client.post(PATH, content=body + b" ", headers=signed_headers(body))
    assert response.status_code == 403
    assert count_deliveries(db) == 0


@pytest.mark.parametrize("body", [b"not json", b"[]", b"{}", b'{"entry": []}', b"\xff", b"NaN"])
def test_invalid_signed_payloads_are_not_captured(client, db, body):
    assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 400
    assert count_deliveries(db) == 0


def test_request_limits(client, db):
    assert (
        client.post(PATH, content=b"{}", headers={"Content-Type": "text/plain"}).status_code == 415
    )
    body = b" " * (4 * 1024 * 1024 + 1)
    assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 413
    assert count_deliveries(db) == 0


def test_unconfigured_webhook_fails_closed(client, db, monkeypatch):
    monkeypatch.setattr(whatsapp_webhooks, "get_settings", lambda: Settings())
    assert client.get(PATH).status_code == 503
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 503
    assert count_deliveries(db) == 0


def test_capture_failure_is_not_acknowledged(client, monkeypatch):
    def fail(*args):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(whatsapp_webhooks, "capture_delivery", fail)
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 500


def test_commit_failure_is_not_acknowledged_or_persisted(client, db):
    def failing_transaction():
        try:
            yield db
            raise RuntimeError("commit failed")
        finally:
            db.rollback()

    app.dependency_overrides[get_db] = failing_transaction
    body = b'{"object":"whatsapp_business_account","entry":[]}'
    assert client.post(PATH, content=body, headers=signed_headers(body)).status_code == 500
    assert count_deliveries(db) == 0


def test_cleanup_only_erases_deliveries_older_than_thirty_days(db):
    db.add_all(
        [
            WhatsAppWebhookDelivery(
                payload_hash="a" * 64, raw_body=b"{}", received_at=now() - timedelta(days=31)
            ),
            WhatsAppWebhookDelivery(
                payload_hash="b" * 64, raw_body=b"{}", received_at=now() - timedelta(days=1)
            ),
        ]
    )
    db.commit()
    assert whatsapp_webhooks.erase_expired_deliveries(db) == 1
    db.commit()
    assert db.get(WhatsAppWebhookDelivery, "a" * 64) is None
    assert db.get(WhatsAppWebhookDelivery, "b" * 64) is not None
