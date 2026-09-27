from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import TRANSACTIONAL_DB, admin
from app.schemas.domain import (
    BrandInput,
    BrandOut,
    CategoryInput,
    CategoryOut,
    ProductInput,
    ProductOut,
    ProductPage,
    VariantInput,
    VariantOut,
)
from app.services import catalogue

router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.get("/brands", response_model=list[BrandOut])
def admin_brands(db: Session = TRANSACTIONAL_DB):
    return catalogue.list_brands(db, admin=True)


@router.post("/brands", response_model=BrandOut, status_code=201)
def create_brand(data: BrandInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_brand(db, data)


@router.put("/brands/{brand_id}", response_model=BrandOut)
def edit_brand(brand_id: int, data: BrandInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_brand(db, data, brand_id)


@router.get("/categories", response_model=list[CategoryOut])
def admin_categories(db: Session = TRANSACTIONAL_DB):
    return catalogue.list_categories(db, admin=True)


@router.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_category(db, data)


@router.put("/categories/{category_id}", response_model=CategoryOut)
def edit_category(category_id: int, data: CategoryInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_category(db, data, category_id)


@router.get("/products", response_model=ProductPage)
def admin_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: str | None = Query(None, max_length=200),
    category_id: int | None = None,
    brand_id: int | None = None,
    available: bool | None = None,
    active: bool | None = None,
    db: Session = TRANSACTIONAL_DB,
):
    return catalogue.list_products(
        db, page, page_size, q, category_id, available, active, True, brand_id
    )


@router.get("/products/{product_id}", response_model=ProductOut)
def admin_product(product_id: int, db: Session = TRANSACTIONAL_DB):
    return catalogue.product_out(catalogue.get_product(db, product_id, True), True)


@router.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_product(db, data)


@router.put("/products/{product_id}", response_model=ProductOut)
def edit_product(product_id: int, data: ProductInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_product(db, data, product_id)


@router.post("/products/{product_id}/variants", response_model=VariantOut, status_code=201)
def create_variant(product_id: int, data: VariantInput, db: Session = TRANSACTIONAL_DB):
    return catalogue.save_variant(db, product_id, data)


@router.put("/products/{product_id}/variants/{variant_id}", response_model=VariantOut)
def edit_variant(
    product_id: int,
    variant_id: int,
    data: VariantInput,
    db: Session = TRANSACTIONAL_DB,
):
    return catalogue.save_variant(db, product_id, data, variant_id)
