from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, customer
from app.models.domain import Customer
from app.schemas.domain import AddressInput, AddressOut
from app.services import address_suggestion, customer_data

router = APIRouter(prefix="/api/v1")


@router.get("/addresses", response_model=list[AddressOut], tags=["customer"])
def addresses(current: Customer = Depends(customer), db: Session = TRANSACTIONAL_DB):
    return customer_data.list_addresses(db, current.id)


@router.get("/addresses/reverse-geocode", tags=["customer"])
def reverse_geocode(
    latitude: Decimal = Query(ge=-90, le=90),
    longitude: Decimal = Query(ge=-180, le=180),
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return address_suggestion.suggest_address(db, current.id, latitude, longitude)


@router.post("/addresses", response_model=AddressOut, status_code=201, tags=["customer"])
def create_address(
    data: AddressInput,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return customer_data.create_address(db, current.id, data)


@router.put("/addresses/{address_id}", response_model=AddressOut, tags=["customer"])
def edit_address(
    address_id: int,
    data: AddressInput,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    return customer_data.update_address(db, current.id, address_id, data)


@router.delete("/addresses/{address_id}", status_code=204, tags=["customer"])
def delete_address(
    address_id: int,
    current: Customer = Depends(customer),
    db: Session = TRANSACTIONAL_DB,
):
    customer_data.delete_address(db, current.id, address_id)
