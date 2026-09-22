from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import SessionLocal
from app.models.domain import Admin, AuthSession, Customer, now
from app.services.auth import aware, digest


def get_db():
    with SessionLocal() as db:
        try:
            yield db
        except Exception:
            db.rollback()
            raise


def session_for(request: Request, db: Session, admin: bool):
    if admin:
        authorization = request.headers.get("authorization", "")
        bearer = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
        token = bearer or request.cookies.get("gg_admin", "")
        if not bearer and request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("origin") != get_settings().admin_origin:
                raise DomainError("FORBIDDEN", "Untrusted request origin", 403)
    else:
        authorization = request.headers.get("authorization", "")
        token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
    session = db.get(AuthSession, digest(token)) if token else None
    if (
        session is None
        or aware(session.expires_at) <= now()
        or (session.admin_id is None if admin else session.customer_id is None)
    ):
        raise DomainError("UNAUTHENTICATED", "Please sign in to continue", 401)
    return session


def customer(request: Request, db: Session = Depends(get_db)) -> Customer:
    return db.get(Customer, session_for(request, db, False).customer_id)


def admin(request: Request, db: Session = Depends(get_db)) -> Admin:
    return db.get(Admin, session_for(request, db, True).admin_id)


def owned(db, model, object_id, customer_id):
    value = db.get(model, object_id)
    if value is None or value.customer_id != customer_id:
        raise DomainError("NOT_FOUND", "Resource not found", 404)
    return value
