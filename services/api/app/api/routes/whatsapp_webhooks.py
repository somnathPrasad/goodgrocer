from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB
from app.core.errors import DomainError
from app.services import whatsapp_webhooks

router = APIRouter(prefix="/api/v1/webhooks/whatsapp", tags=["whatsapp-webhooks"])
MAX_WEBHOOK_BYTES = 4 * 1024 * 1024


@router.get("", response_class=PlainTextResponse)
def verify_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    return whatsapp_webhooks.verify_subscription(mode, token, challenge)


async def webhook_body(request: Request) -> bytes:
    if (
        request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
        != "application/json"
    ):
        raise DomainError("INVALID_WEBHOOK_CONTENT_TYPE", "Expected application/json", 415)
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_WEBHOOK_BYTES:
            raise DomainError("WEBHOOK_TOO_LARGE", "Webhook payload exceeds 4 MiB", 413)
        body.extend(chunk)
    return bytes(body)


@router.post("", response_class=PlainTextResponse)
def receive_webhook(
    request: Request,
    raw_body: bytes = Depends(webhook_body),
    db: Session = TRANSACTIONAL_DB,
):
    whatsapp_webhooks.capture_delivery(db, raw_body, request.headers.get("x-hub-signature-256"))
    # The function-scoped database dependency commits before the response is sent.
    return "EVENT_RECEIVED"
