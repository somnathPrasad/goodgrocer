import hashlib
import hmac
import json
from datetime import timedelta

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.domain import WhatsAppWebhookDelivery, now


def verify_subscription(mode: str | None, token: str | None, challenge: str | None) -> str:
    expected = get_settings().whatsapp_webhook_verify_token
    if expected is None:
        raise DomainError("WHATSAPP_NOT_CONFIGURED", "WhatsApp webhook is not configured", 503)
    if (
        mode != "subscribe"
        or token is None
        or not hmac.compare_digest(token.encode(), expected.get_secret_value().encode())
    ):
        raise DomainError("INVALID_WEBHOOK_VERIFICATION", "Webhook verification failed", 403)
    if not challenge:
        raise DomainError("INVALID_WEBHOOK_CHALLENGE", "Missing webhook challenge", 400)
    return challenge


def capture_delivery(db: Session, raw_body: bytes, signature: str | None) -> None:
    secret = get_settings().whatsapp_app_secret
    if secret is None:
        raise DomainError("WHATSAPP_NOT_CONFIGURED", "WhatsApp webhook is not configured", 503)
    expected = (
        "sha256="
        + hmac.new(secret.get_secret_value().encode(), raw_body, hashlib.sha256).hexdigest()
    )
    if signature is None or not hmac.compare_digest(signature.encode(), expected.encode()):
        raise DomainError("INVALID_WEBHOOK_SIGNATURE", "Webhook signature verification failed", 403)
    try:
        payload = json.loads(raw_body.decode("utf-8"), parse_constant=reject_json_constant)
    except (ValueError, RecursionError):
        raise DomainError("INVALID_WEBHOOK_PAYLOAD", "Invalid webhook JSON", 400) from None
    if (
        not isinstance(payload, dict)
        or payload.get("object") != "whatsapp_business_account"
        or not isinstance(payload.get("entry"), list)
        or not all(isinstance(entry, dict) for entry in payload["entry"])
    ):
        raise DomainError("INVALID_WEBHOOK_PAYLOAD", "Invalid WhatsApp webhook envelope", 400)
    # Exact retries are safe across API workers. A future event consumer must also
    # deduplicate message/status IDs when Meta re-batches the same updates.
    db.execute(
        insert(WhatsAppWebhookDelivery)
        .values(payload_hash=hashlib.sha256(raw_body).hexdigest(), raw_body=raw_body)
        .on_conflict_do_nothing(index_elements=[WhatsAppWebhookDelivery.payload_hash])
    )


def reject_json_constant(value: str):
    raise ValueError("Invalid JSON constant")


def erase_expired_deliveries(db: Session) -> int:
    result = db.execute(
        delete(WhatsAppWebhookDelivery).where(
            WhatsAppWebhookDelivery.received_at <= now() - timedelta(days=30)
        )
    )
    return result.rowcount
