from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import event

from app.models.domain import Product, ProductVariant
from app.schemas.domain import CategoryInput, ProductInput, VariantInput
from app.services import catalogue


@pytest.mark.parametrize(
    "image_url",
    [None, "", "/media/apple.jpg", "https://example.com/apple.jpg"],
)
def test_product_input_accepts_supported_image_values(image_url):
    data = {"name": "Apple", "slug": "apple", "brand_id": 1, "image_url": image_url}
    assert ProductInput.model_validate(data).image_url == image_url


def test_product_input_rejects_unsupported_image_values():
    with pytest.raises((ValidationError, ValueError), match="uploaded media path"):
        ProductInput.model_validate(
            {
                "name": "Apple",
                "slug": "apple",
                "brand_id": 1,
                "image_url": "http://example.com/apple.jpg",
            }
        )


@pytest.mark.parametrize("mrp,price", [("-1", "0"), ("10", "-1"), ("10", "11"), ("10", "1.001")])
def test_variant_input_rejects_invalid_prices(mrp, price):
    with pytest.raises(ValidationError):
        VariantInput(name="Test", mrp=mrp, selling_price=price)


def test_customer_catalogue_filters_searches_and_paginates(db, data):
    for category in data["categories"]:
        result = catalogue.list_products(
            db,
            category_id=category.id,
            q="ric",
            page_size=1,
        )
        assert result["total"] == 1
        assert len(result["items"][0].categories) == 2

    assert catalogue.list_products(db, page=2, page_size=1)["items"] == []
    assert catalogue.list_products(db, q="absent")["total"] == 0

    data["product"].active = False
    db.flush()
    assert catalogue.list_products(db)["items"] == []


def test_owner_catalogue_updates_category_order_and_variant_visibility(db, data):
    category = data["categories"][0]
    catalogue.save_category(
        db,
        CategoryInput(name="Fresh edited", slug="fresh", display_order=99, active=True),
        category.id,
    )
    assert catalogue.list_categories(db)[-1].id == category.id

    catalogue.save_variant(
        db,
        data["product"].id,
        VariantInput(name="1 kg", mrp="100", selling_price="99", active=False),
        data["variant"].id,
    )
    assert catalogue.product_out(data["product"]).variants == []


def test_catalogue_query_count_does_not_grow_per_product(db, data):
    for index in range(12):
        product = Product(
            name=f"Item {index}",
            slug=f"item-{index}",
            brand_id=data["product"].brand_id,
            categories=data["categories"],
        )
        db.add(product)
        db.flush()
        db.add(
            ProductVariant(
                product_id=product.id,
                name="Regular",
                mrp=Decimal("10"),
                selling_price=Decimal("9"),
            )
        )
    db.flush()
    db.expire_all()
    statements = []

    def record(connection, cursor, statement, parameters, context, many):
        statements.append(statement)

    event.listen(db.bind, "before_cursor_execute", record)
    try:
        result = catalogue.list_products(db, page_size=24)
        assert result["total"] == 13
        assert len(statements) <= 6
    finally:
        event.remove(db.bind, "before_cursor_execute", record)
