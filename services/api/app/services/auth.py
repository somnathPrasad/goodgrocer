import hashlib
import hmac
import secrets
from datetime import UTC, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.domain import OTP, Admin, AuthSession, Customer, RateLimit, now
from app.services.providers import otp_provider

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


def code_digest(phone: str, code: str):
    return hmac.new(
        get_settings().secret_key.encode(),
        (phone + ":" + code).encode(),
        hashlib.sha256,
    ).hexdigest()


def request_otp(db: Session, phone: str, ip: str):
    provider = otp_provider()
    rate_limit(db, "otp-ip:" + digest(ip), 20, 3600)
    rate_limit(db, "otp-phone:" + phone, 5, 3600)
    row = db.scalar(select(OTP).where(OTP.phone_number == phone).with_for_update())
    if row and aware(row.sent_at) > now() - timedelta(seconds=60):
        raise DomainError("OTP_RESEND", "Wait 60 seconds before requesting another code", 429)
    code = f"{secrets.randbelow(1000000):06d}"
    if row is None:
        row = OTP(phone_number=phone)
        db.add(row)
    row.code_hash, row.expires_at = (
        code_digest(phone, code),
        now() + timedelta(minutes=5),
    )
    row.sent_at, row.attempts = now(), 0
    provider.send(phone, code)
    db.commit()
    return {
        "message": "Code requested. It expires in 5 minutes.",
        "development_code": code
        if get_settings().environment != "production"
        and get_settings().otp_provider == "development"
        else None,
    }


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


def verify_otp(db: Session, phone: str, code: str):
    row = db.scalar(select(OTP).where(OTP.phone_number == phone).with_for_update())
    if row is None or aware(row.expires_at) < now() or row.attempts >= 5:
        raise DomainError(
            "INVALID_OTP",
            "Code expired or attempts exhausted. Request a new code.",
            401,
        )
    row.attempts += 1
    if not hmac.compare_digest(row.code_hash, code_digest(phone, code)):
        db.commit()
        raise DomainError("INVALID_OTP", "Incorrect code", 401)
    # Keep the row to retain the resend cooldown after successful verification.
    row.attempts = 5
    customer = db.scalar(select(Customer).where(Customer.phone_number == phone))
    if customer is None:
        customer = Customer(phone_number=phone)
        db.add(customer)
        db.flush()
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
