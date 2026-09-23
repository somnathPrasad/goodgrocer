from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models.domain import (
    Address,
    AuthSession,
    Customer,
    Favourite,
    Order,
    PaymentAttempt,
    RateLimit,
    now,
)
from app.services.auth import digest, rate_limit, verify_google_identity

TERMINAL_ORDER_STATUSES = {"DELIVERED", "CANCELLED"}
DELIVERY_DETAILS_RETENTION_DAYS = 30


def erase_delivery_details(order: Order, erased_at=None):
    order.address_snapshot = None
    order.customer_phone = None
    order.delivery_details_erase_at = erased_at or now()


def delete_customer(
    db: Session,
    id_token: str,
    ip: str,
    current_customer_id: int | None = None,
):
    rate_limit(db, "customer-delete-ip:" + digest(ip), 100, 3600)
    subject = verify_google_identity(id_token)["sub"]
    subject_rate_key = "customer-delete-subject:" + digest(subject)
    rate_limit(db, subject_rate_key, 5, 3600)

    if current_customer_id is not None:
        current = db.scalar(
            select(Customer).where(Customer.id == current_customer_id).with_for_update()
        )
        if current is not None and current.google_subject != subject:
            raise DomainError(
                "GOOGLE_ACCOUNT_MISMATCH",
                "Choose the Google account currently used with Goodgrocer.",
                409,
            )

    customer = db.scalar(
        select(Customer).where(Customer.google_subject == subject).with_for_update()
    )
    if customer is None:
        db.execute(delete(RateLimit).where(RateLimit.key == subject_rate_key))
        db.commit()
        return

    deleted_at = now()
    retained_orders = db.scalars(
        select(Order).where(Order.customer_id == customer.id).order_by(Order.id).with_for_update()
    ).all()
    order_ids = [order.id for order in retained_orders]
    if order_ids:
        db.execute(delete(PaymentAttempt).where(PaymentAttempt.order_id.in_(order_ids)))
    for order in retained_orders:
        order.customer_id = None
        order.customer_deleted_at = deleted_at
        if order.status in TERMINAL_ORDER_STATUSES:
            erase_delivery_details(order, deleted_at)
        else:
            order.delivery_details_erase_at = deleted_at + timedelta(
                days=DELIVERY_DETAILS_RETENTION_DAYS
            )
    db.flush()

    db.execute(delete(AuthSession).where(AuthSession.customer_id == customer.id))
    db.execute(delete(Address).where(Address.customer_id == customer.id))
    db.execute(delete(Favourite).where(Favourite.customer_id == customer.id))
    db.execute(delete(RateLimit).where(RateLimit.key == subject_rate_key))
    db.delete(customer)
    db.commit()


def erase_expired_delivery_details(db: Session, as_of=None) -> int:
    cutoff = as_of or now()
    rows = db.scalars(
        select(Order)
        .where(
            Order.customer_deleted_at.is_not(None),
            Order.delivery_details_erase_at <= cutoff,
            Order.customer_phone.is_not(None),
        )
        .order_by(Order.id)
        .with_for_update()
    ).all()
    for order in rows:
        erase_delivery_details(order, order.delivery_details_erase_at)
    db.commit()
    return len(rows)
