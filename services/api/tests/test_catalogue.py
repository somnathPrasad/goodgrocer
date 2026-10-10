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


@pytest.mark.parametrize(
    "unavailable_reason",
    ["product_unavailable", "variant_unavailable", "variant_inactive", "no_variants"],
)
def test_unavailable_products_are_hidden_from_browsing_but_searchable(
    client, db, data, unavailable_reason
):
    product = data["product"]
    if unavailable_reason == "product_unavailable":
        product.available = False
    elif unavailable_reason == "variant_unavailable":
        data["variant"].available = False
    elif unavailable_reason == "variant_inactive":
        data["variant"].active = False
    else:
        db.delete(data["variant"])
    db.flush()

    for params in ({}, {"q": ""}, {"q": "   "}, {"category_id": data["categories"][0].id}):
        response = client.get("/api/v1/products", params=params)
        assert response.status_code == 200
        assert response.json()["items"] == []
        assert response.json()["total"] == 0

    for params in ({"q": "ric"}, {"q": "ric", "category_id": data["categories"][0].id}):
        response = client.get("/api/v1/products", params=params)
        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == [product.id]
        assert response.json()["total"] == 1

    assert client.get(f"/api/v1/products/{product.id}").status_code == 200
    assert catalogue.list_products(db, admin=True)["total"] == 1
    product.active = False
    db.flush()
    assert client.get("/api/v1/products", params={"q": "ric"}).json()["items"] == []


def test_browsing_filters_before_pagination_and_retains_unavailable_choices(db, data):
    data["product"].available = False
    visible_ids = []
    for index in range(2):
        product = Product(
            name=f"Rice {index}",
            slug=f"rice-{index}",
            brand_id=data["product"].brand_id,
            categories=data["categories"],
        )
        db.add(product)
        db.flush()
        visible_ids.append(product.id)
        for available in (True, True, False):
            db.add(
                ProductVariant(
                    product_id=product.id,
                    name="Regular",
                    mrp=Decimal("10"),
                    selling_price=Decimal("9"),
                    available=available,
                )
            )
    db.flush()

    for page, product_id in enumerate(visible_ids, start=1):
        result = catalogue.list_products(db, page=page, page_size=1)
        assert result["total"] == 2
        assert [item.id for item in result["items"]] == [product_id]
        assert [variant.available for variant in result["items"][0].variants] == [True, True, False]
    assert catalogue.list_products(db, page=3, page_size=1)["items"] == []


def test_explicit_availability_filters_cannot_bypass_browsing_rule(db, data):
    data["product"].available = False
    db.flush()
    assert catalogue.list_products(db, available=False)["total"] == 0
    assert catalogue.list_products(db, q="ric", available=False)["total"] == 1
    assert catalogue.list_products(db, admin=True, available=False)["total"] == 1

    data["product"].available = True
    data["variant"].available = False
    db.flush()
    assert catalogue.list_products(db, available=True)["total"] == 0
    assert catalogue.list_products(db, q="ric", available=True)["total"] == 1
    assert catalogue.list_products(db, admin=True, available=True)["total"] == 1


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
