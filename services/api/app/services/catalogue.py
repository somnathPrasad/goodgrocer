from sqlalchemy import func, select

from app.core.errors import DomainError
from app.models.domain import Brand, Category, Product, ProductCategory, ProductVariant
from app.schemas.domain import ProductOut


def product_out(product, admin=False):
    result = ProductOut.model_validate(product)
    if not admin:
        result.variants = [v for v in result.variants if v.active]
        result.categories = [c for c in result.categories if c.active]
    return result


def list_products(
    db,
    page=1,
    page_size=24,
    q=None,
    category_id=None,
    available=None,
    active=None,
    admin=False,
    brand_id=None,
):
    query = select(Product)
    if not admin:
        query = query.where(Product.active.is_(True))
    elif active is not None:
        query = query.where(Product.active == active)
    if q:
        query = query.where(
            Product.name.ilike("%" + q.replace("%", r"\%").replace("_", r"\_") + "%")
        )
    if category_id:
        query = query.where(
            Product.id.in_(
                select(ProductCategory.product_id)
                .join(Category)
                .where(
                    Category.id == category_id,
                    Category.active.is_(True) if not admin else True,
                )
            )
        )
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
    if available is not None:
        query = query.where(Product.available == available)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    products = db.scalars(
        query.order_by(Product.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [product_out(p, admin) for p in products],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_product(db, product_id, admin=False):
    product = db.get(Product, product_id)
    if product is None or (not admin and not product.active):
        raise DomainError("NOT_FOUND", "Product not found", 404)
    return product


def save_product(db, data, product_id=None):
    if not db.get(Brand, data.brand_id):
        raise DomainError("INVALID_BRAND", "Choose an existing brand")
    ids = set(data.category_ids)
    categories = db.scalars(select(Category).where(Category.id.in_(ids))).all()
    if len(categories) != len(ids):
        raise DomainError("INVALID_CATEGORY", "Choose existing categories")
    values = data.model_dump(exclude={"category_ids"})
    product = get_product(db, product_id, True) if product_id else Product()
    for key, value in values.items():
        setattr(product, key, value)
    product.categories = list(categories)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_out(product, True)


def save_variant(db, product_id, data, variant_id=None):
    get_product(db, product_id, True)
    variant = (
        db.get(ProductVariant, variant_id) if variant_id else ProductVariant(product_id=product_id)
    )
    if variant is None or variant.product_id != product_id:
        raise DomainError("NOT_FOUND", "Variant not found", 404)
    for key, value in data.model_dump().items():
        setattr(variant, key, value)
    db.add(variant)
    db.commit()
    return variant
