from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, customer
from app.models.domain import Customer
from app.schemas.domain import ProductOut
from app.services import customer_data

router = APIRouter(prefix="/api/v1")


@router.get("/favourites", response_model=list[ProductOut], tags=["customer"])
def favourites(current: Customer = Depends(customer), db: Session = TRANSACTIONAL_DB):
    return customer_data.list_favourites(db, current.id)


@router.put("/favourites/{product_id}", status_code=204, tags=["customer"])
def favourite(
    product_id: int,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    customer_data.add_favourite(db, current.id, product_id)


@router.delete("/favourites/{product_id}", status_code=204, tags=["customer"])
def unfavourite(
    product_id: int,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    customer_data.remove_favourite(db, current.id, product_id)
