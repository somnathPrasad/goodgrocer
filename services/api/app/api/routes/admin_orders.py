from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, admin
from app.schemas.domain import OrderOut, TransitionInput
from app.services import orders

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.get("/orders", response_model=list[OrderOut])
def admin_orders(
    page: int = Query(1, ge=1),
    status: Literal["PLACED", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    | None = None,
    db: Session = TRANSACTIONAL_DB,
):
    return orders.list_for_owner(db, page, status)


@router.get("/orders/{order_id}", response_model=OrderOut)
def admin_order(order_id: int, db: Session = TRANSACTIONAL_DB):
    return orders.get_for_owner(db, order_id)


@router.post("/orders/{order_id}/status", response_model=OrderOut)
def change_status(order_id: int, data: TransitionInput, db: Session = TRANSACTIONAL_DB):
    return orders.transition(db, order_id, data)


@router.post("/orders/{order_id}/mark-paid", response_model=OrderOut)
def mark_paid(order_id: int, db: Session = TRANSACTIONAL_DB):
    return orders.mark_cash_received(db, order_id)
