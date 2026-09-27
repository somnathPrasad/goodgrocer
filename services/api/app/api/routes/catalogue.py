from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB
from app.schemas.domain import BrandOut, CategoryOut, ProductOut, ProductPage
from app.services import catalogue

router = APIRouter(prefix="/api/v1")


@router.get("/brands", response_model=list[BrandOut], tags=["catalogue"])
def brands(db: Session = TRANSACTIONAL_DB):
    return catalogue.list_brands(db)


@router.get("/categories", response_model=list[CategoryOut], tags=["catalogue"])
def categories(db: Session = TRANSACTIONAL_DB):
    return catalogue.list_categories(db)


@router.get("/products", response_model=ProductPage, tags=["catalogue"])
def products(
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: str | None = Query(None, max_length=200),
    category_id: int | None = None,
    available: bool | None = None,
    db: Session = TRANSACTIONAL_DB,
):
    return catalogue.list_products(db, page, page_size, q, category_id, available)


@router.get("/products/{product_id}", response_model=ProductOut, tags=["catalogue"])
def product(product_id: int, db: Session = TRANSACTIONAL_DB):
    return catalogue.product_out(catalogue.get_product(db, product_id))
