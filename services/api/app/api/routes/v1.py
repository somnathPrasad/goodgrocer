from datetime import datetime, time
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.dependencies import admin, customer, get_db, owned, session_for
from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.domain import (
    Address,
    Brand,
    Category,
    Customer,
    Favourite,
    Order,
    Product,
)
from app.schemas.domain import (
    AddressInput,
    AddressOut,
    BrandInput,
    BrandOut,
    CategoryInput,
    CategoryOut,
    CheckoutInput,
    GoogleLoginInput,
    LoginInput,
    OrderInput,
    OrderOut,
    ProductInput,
    ProductOut,
    ProductPage,
    QuoteOut,
    ReorderOut,
    TokenResponse,
    TransitionInput,
    VariantInput,
    VariantOut,
)
from app.services import auth, catalogue, orders
from app.services.providers import image_storage, payment_provider

router = APIRouter(prefix="/api/v1")
owner = APIRouter(prefix="/admin", dependencies=[Depends(admin)], tags=["admin"])


@router.get("/config")
def config():
    settings = get_settings()
    return {
        "online_upi_enabled": settings.payment_provider != "disabled",
        "development": settings.environment != "production",
        "delivery_fee": str(settings.delivery_fee),
    }


@router.get("/brands", response_model=list[BrandOut], tags=["catalogue"])
def brands(db: Session = Depends(get_db)):
    return db.scalars(select(Brand).where(Brand.active.is_(True)).order_by(Brand.name)).all()


@router.get("/categories", response_model=list[CategoryOut], tags=["catalogue"])
def categories(db: Session = Depends(get_db)):
    return db.scalars(
        select(Category)
        .where(Category.active.is_(True))
        .order_by(Category.display_order, Category.id)
    ).all()


@router.get("/products", response_model=ProductPage, tags=["catalogue"])
def products(
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: str | None = Query(None, max_length=200),
    category_id: int | None = None,
    available: bool | None = None,
    db: Session = Depends(get_db),
):
    return catalogue.list_products(db, page, page_size, q, category_id, available)


@router.get("/products/{product_id}", response_model=ProductOut, tags=["catalogue"])
def product(product_id: int, db: Session = Depends(get_db)):
    return catalogue.product_out(catalogue.get_product(db, product_id))


@router.post("/auth/google", response_model=TokenResponse, tags=["auth"])
def google_login(data: GoogleLoginInput, request: Request, db: Session = Depends(get_db)):
    return auth.google_login(db, data.id_token, request.client.host)


@router.post("/auth/logout", status_code=204, tags=["auth"])
def logout(
    request: Request,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    db.delete(session_for(request, db, False))
    db.commit()


@router.get("/addresses", response_model=list[AddressOut], tags=["customer"])
def addresses(current: Customer = Depends(customer), db: Session = Depends(get_db)):
    return db.scalars(
        select(Address).where(Address.customer_id == current.id).order_by(Address.id)
    ).all()


@router.post("/addresses", response_model=AddressOut, status_code=201, tags=["customer"])
def create_address(
    data: AddressInput,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    row = Address(customer_id=current.id, **data.model_dump())
    db.add(row)
    db.commit()
    return row


@router.put("/addresses/{address_id}", response_model=AddressOut, tags=["customer"])
def edit_address(
    address_id: int,
    data: AddressInput,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    row = owned(db, Address, address_id, current.id)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return row


@router.delete("/addresses/{address_id}", status_code=204, tags=["customer"])
def delete_address(
    address_id: int,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    db.delete(owned(db, Address, address_id, current.id))
    db.commit()


@router.get("/favourites", response_model=list[ProductOut], tags=["customer"])
def favourites(current: Customer = Depends(customer), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Product)
        .join(Favourite)
        .where(Favourite.customer_id == current.id, Product.active.is_(True))
        .order_by(Product.id)
    ).all()
    return [catalogue.product_out(p) for p in rows]


@router.put("/favourites/{product_id}", status_code=204, tags=["customer"])
def favourite(
    product_id: int,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    catalogue.get_product(db, product_id)
    db.scalar(select(Customer).where(Customer.id == current.id).with_for_update())
    if not db.get(Favourite, (current.id, product_id)):
        db.add(Favourite(customer_id=current.id, product_id=product_id))
    db.commit()


@router.delete("/favourites/{product_id}", status_code=204, tags=["customer"])
def unfavourite(
    product_id: int,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    row = db.get(Favourite, (current.id, product_id))
    if row:
        db.delete(row)
        db.commit()


@router.post("/checkout/quote", response_model=QuoteOut, tags=["orders"])
def quote(
    data: CheckoutInput,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    return orders.quote(db, current, data)


@router.post("/orders", response_model=OrderOut, status_code=201, tags=["orders"])
def place_order(
    data: OrderInput,
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    return orders.place_order(db, current, data)


@router.get("/orders", response_model=list[OrderOut], tags=["orders"])
def order_list(
    page: int = Query(1, ge=1),
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Order)
        .where(Order.customer_id == current.id)
        .order_by(Order.id.desc())
        .offset((page - 1) * 20)
        .limit(20)
    ).all()


@router.get("/orders/{order_id}", response_model=OrderOut, tags=["orders"])
def order_detail(
    order_id: int, current: Customer = Depends(customer), db: Session = Depends(get_db)
):
    return owned(db, Order, order_id, current.id)


@router.post("/orders/{order_id}/reorder", response_model=ReorderOut, tags=["orders"])
def reorder(order_id: int, current: Customer = Depends(customer), db: Session = Depends(get_db)):
    return orders.reorder(db, owned(db, Order, order_id, current.id))


@router.post("/orders/{order_id}/development-payment", response_model=OrderOut, tags=["payments"])
def dev_payment(
    order_id: int,
    outcome: Literal["PAID", "FAILED"],
    current: Customer = Depends(customer),
    db: Session = Depends(get_db),
):
    payment_provider()
    row = db.scalar(
        select(Order).where(Order.id == order_id, Order.customer_id == current.id).with_for_update()
    )
    if row is None:
        raise DomainError("NOT_FOUND", "Order not found", 404)
    if (
        row.status != "PLACED"
        or row.payment_method != "ONLINE_UPI"
        or row.payment_status != "PENDING"
    ):
        raise DomainError("INVALID_PAYMENT", "This payment cannot be changed", 409)
    attempt = row.payment_attempts[-1]
    if attempt.provider != "development":
        raise DomainError("INVALID_PAYMENT", "Not a development payment", 409)
    row.payment_status = attempt.status = outcome
    db.commit()
    return row


@router.post("/admin/auth/login", tags=["admin-auth"])
def admin_login(
    data: LoginInput,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    if request.headers.get("origin") != get_settings().admin_origin:
        raise DomainError("FORBIDDEN", "Untrusted request origin", 403)
    result = auth.admin_login(db, data.username, data.password, request.client.host)
    response.set_cookie(
        "gg_admin",
        result["token"],
        httponly=True,
        secure=get_settings().environment == "production",
        samesite="strict",
        max_age=43200,
        path="/api/v1/admin",
    )
    return {"message": "Signed in"}


@router.post("/admin/auth/mobile-login", response_model=TokenResponse, tags=["admin-auth"])
def admin_mobile_login(data: LoginInput, request: Request, db: Session = Depends(get_db)):
    # Native clients have no Origin. Reject browser-originated requests here.
    if request.headers.get("origin"):
        raise DomainError("FORBIDDEN", "Use the browser sign-in endpoint", 403)
    return auth.admin_login(db, data.username, data.password, request.client.host)


@owner.post("/auth/logout", status_code=204)
def admin_logout(request: Request, response: Response, db: Session = Depends(get_db)):
    db.delete(session_for(request, db, True))
    db.commit()
    response.delete_cookie("gg_admin", path="/api/v1/admin")


@owner.get("/me")
def admin_me():
    return {"authenticated": True}


@owner.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    today = datetime.combine(
        datetime.now(ZoneInfo("Asia/Kolkata")).date(),
        time.min,
        tzinfo=ZoneInfo("Asia/Kolkata"),
    )
    return {
        "awaiting_action": db.scalar(
            select(func.count()).select_from(Order).where(Order.status == "PLACED")
        ),
        "today_orders": db.scalar(
            select(func.count()).select_from(Order).where(Order.created_at >= today)
        ),
        "unavailable_products": db.scalar(
            select(func.count())
            .select_from(Product)
            .where(Product.active.is_(True), Product.available.is_(False))
        ),
        "recent_orders": [
            OrderOut.model_validate(o)
            for o in db.scalars(select(Order).order_by(Order.id.desc()).limit(8))
        ],
    }


@owner.get("/brands", response_model=list[BrandOut])
def admin_brands(db: Session = Depends(get_db)):
    return db.scalars(select(Brand).order_by(Brand.name)).all()


@owner.post("/brands", response_model=BrandOut, status_code=201)
def create_brand(data: BrandInput, db: Session = Depends(get_db)):
    row = Brand(**data.model_dump())
    db.add(row)
    db.commit()
    return row


@owner.put("/brands/{brand_id}", response_model=BrandOut)
def edit_brand(brand_id: int, data: BrandInput, db: Session = Depends(get_db)):
    row = db.get(Brand, brand_id)
    if row is None:
        raise DomainError("NOT_FOUND", "Brand not found", 404)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return row


@owner.get("/categories", response_model=list[CategoryOut])
def admin_categories(db: Session = Depends(get_db)):
    return db.scalars(select(Category).order_by(Category.display_order, Category.id)).all()


@owner.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryInput, db: Session = Depends(get_db)):
    row = Category(**data.model_dump())
    db.add(row)
    db.commit()
    return row


@owner.put("/categories/{category_id}", response_model=CategoryOut)
def edit_category(category_id: int, data: CategoryInput, db: Session = Depends(get_db)):
    row = db.get(Category, category_id)
    if row is None:
        raise DomainError("NOT_FOUND", "Category not found", 404)
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return row


@owner.get("/products", response_model=ProductPage)
def admin_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: str | None = Query(None, max_length=200),
    category_id: int | None = None,
    brand_id: int | None = None,
    available: bool | None = None,
    active: bool | None = None,
    db: Session = Depends(get_db),
):
    return catalogue.list_products(
        db, page, page_size, q, category_id, available, active, True, brand_id
    )


@owner.get("/products/{product_id}", response_model=ProductOut)
def admin_product(product_id: int, db: Session = Depends(get_db)):
    return catalogue.product_out(catalogue.get_product(db, product_id, True), True)


@owner.post("/products", response_model=ProductOut, status_code=201)
def create_product(data: ProductInput, db: Session = Depends(get_db)):
    return catalogue.save_product(db, data)


@owner.put("/products/{product_id}", response_model=ProductOut)
def edit_product(product_id: int, data: ProductInput, db: Session = Depends(get_db)):
    return catalogue.save_product(db, data, product_id)


@owner.post("/products/{product_id}/variants", response_model=VariantOut, status_code=201)
def create_variant(product_id: int, data: VariantInput, db: Session = Depends(get_db)):
    return catalogue.save_variant(db, product_id, data)


@owner.put("/products/{product_id}/variants/{variant_id}", response_model=VariantOut)
def edit_variant(
    product_id: int, variant_id: int, data: VariantInput, db: Session = Depends(get_db)
):
    return catalogue.save_variant(db, product_id, data, variant_id)


@owner.post("/images")
def upload(file: UploadFile):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise DomainError("INVALID_IMAGE", "Upload JPEG, PNG or WebP")
    return {"image_url": image_storage().save(file.file.read(5 * 1024 * 1024 + 1))}


@owner.get("/orders", response_model=list[OrderOut])
def admin_orders(
    page: int = Query(1, ge=1),
    status: Literal["PLACED", "ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]
    | None = None,
    db: Session = Depends(get_db),
):
    query = select(Order)
    if status:
        query = query.where(Order.status == status)
    return db.scalars(query.order_by(Order.id.desc()).offset((page - 1) * 20).limit(20)).all()


@owner.get("/orders/{order_id}", response_model=OrderOut)
def admin_order(order_id: int, db: Session = Depends(get_db)):
    row = db.get(Order, order_id)
    if row is None:
        raise DomainError("NOT_FOUND", "Order not found", 404)
    return row


@owner.post("/orders/{order_id}/status", response_model=OrderOut)
def change_status(order_id: int, data: TransitionInput, db: Session = Depends(get_db)):
    return orders.transition(db, order_id, data)


@owner.post("/orders/{order_id}/mark-paid", response_model=OrderOut)
def mark_paid(order_id: int, db: Session = Depends(get_db)):
    row = db.scalar(select(Order).where(Order.id == order_id).with_for_update())
    if row is None:
        raise DomainError("NOT_FOUND", "Order not found", 404)
    if row.payment_method == "ONLINE_UPI" or row.status == "CANCELLED":
        raise DomainError("INVALID_PAYMENT", "Cannot mark this order paid manually", 409)
    row.payment_status = "PAID"
    db.commit()
    return row


router.include_router(owner)
