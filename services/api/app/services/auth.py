import hashlib
import secrets
from datetime import UTC, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from google.auth.exceptions import TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.domain import Admin, AuthSession, Customer, RateLimit, now

password_hasher = PasswordHasher()
DUMMY_PASSWORD_HASH = password_hasher.hash(secrets.token_urlsafe(32))


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def aware(value):
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def rate_limit(db: Session, key: str, limit: int, seconds: int):
    # PostgreSQL upsert then row lock serializes attempts across workers.
    db.execute(
        insert(RateLimit)
        .values(key=key, count=0, reset_at=now() + timedelta(seconds=seconds))
        .on_conflict_do_nothing()
    )
    row = db.scalar(select(RateLimit).where(RateLimit.key == key).with_for_update())
    if aware(row.reset_at) < now():
        row.count, row.reset_at = 0, now() + timedelta(seconds=seconds)
    if row.count >= limit:
        db.commit()
        raise DomainError("RATE_LIMITED", "Too many attempts. Please try again later.", 429)
    row.count += 1
    db.commit()


def new_session(db: Session, customer_id=None, admin_id=None):
    token = secrets.token_urlsafe(48)
    expiry = now() + timedelta(hours=12 if admin_id else get_settings().session_hours)
    db.add(
        AuthSession(
            token_hash=digest(token),
            customer_id=customer_id,
            admin_id=admin_id,
            expires_at=expiry,
        )
    )
    db.commit()
    return {"token": token, "expires_at": expiry}


def google_login(db: Session, token: str, ip: str):
    client_id = get_settings().google_web_client_id
    if not client_id:
        raise DomainError("GOOGLE_NOT_CONFIGURED", "Google sign-in is not configured", 503)
    rate_limit(db, "google-ip:" + digest(ip), 30, 900)
    try:
        claims = google_id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    except (ValueError, TransportError):
        raise DomainError("INVALID_GOOGLE_TOKEN", "Google sign-in failed", 401) from None
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject or len(subject) > 255:
        raise DomainError("INVALID_GOOGLE_TOKEN", "Google sign-in failed", 401)
    db.execute(
        insert(Customer)
        .values(google_subject=subject)
        .on_conflict_do_nothing(index_elements=[Customer.google_subject])
    )
    customer = db.scalar(select(Customer).where(Customer.google_subject == subject))
    return new_session(db, customer_id=customer.id)


def admin_login(db: Session, username: str, password: str, ip: str):
    rate_limit(db, "admin-ip:" + digest(ip), 20, 900)
    rate_limit(db, "admin-user:" + digest(username), 10, 900)
    admin = db.scalar(select(Admin).where(Admin.username == username))
    try:
        password_hasher.verify(admin.password_hash if admin else DUMMY_PASSWORD_HASH, password)
    except VerificationError:
        raise DomainError("INVALID_CREDENTIALS", "Incorrect username or password", 401) from None
    if admin is None:
        raise DomainError("INVALID_CREDENTIALS", "Incorrect username or password", 401)
    return new_session(db, admin_id=admin.id)
