from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, customer
from app.models.domain import Customer
from app.schemas.domain import (
    CheckoutInput,
    OrderInput,
    OrderOut,
    QuoteOut,
    ReorderOut,
)
from app.services import orders

router = APIRouter(prefix="/api/v1")


@router.post("/checkout/quote", response_model=QuoteOut, tags=["orders"])
def quote(
    data: CheckoutInput,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.quote(db, current, data)


@router.post("/orders", response_model=OrderOut, status_code=201, tags=["orders"])
def place_order(
    data: OrderInput,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.place_order(db, current, data)


@router.get("/orders", response_model=list[OrderOut], tags=["orders"])
def order_list(
    page: int = Query(1, ge=1),
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.list_for_customer(db, current.id, page)


@router.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def order_detail(
    order_id: int,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.get_for_customer(db, current.id, order_id)


@router.post("/orders/{order_id}/reorder", response_model=ReorderOut, tags=["orders"])
def reorder(
    order_id: int,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.reorder(db, current.id, order_id)


@router.post("/orders/{order_id}/development-payment", response_model=OrderOut, tags=["payments"])
def dev_payment(
    order_id: int,
    outcome: Literal["PAID", "FAILED"],
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return orders.complete_development_payment(db, current.id, order_id, outcome)
