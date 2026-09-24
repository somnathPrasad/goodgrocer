from sqlalchemy import func, select

from app.cli import seed_catalogue
from app.models.domain import Brand, Category, Product, ProductVariant
from app.seed_data import BRANDS, CATEGORIES, PRODUCTS


def test_seed_catalogue_is_complete_and_idempotent(db):
    expected_variants = sum(len(product.variants) for product in PRODUCTS)

    first = seed_catalogue(db)
    second = seed_catalogue(db)

    assert (
        first
        == second
        == {
            "brands": len(BRANDS),
            "categories": len(CATEGORIES),
            "products": len(PRODUCTS),
            "variants": expected_variants,
        }
    )
    assert db.scalar(select(func.count()).select_from(Brand)) == len(BRANDS)
    assert db.scalar(select(func.count()).select_from(Category)) == len(CATEGORIES)
    assert db.scalar(select(func.count()).select_from(Product)) == len(PRODUCTS)
    assert db.scalar(select(func.count()).select_from(ProductVariant)) == expected_variants


def test_seed_upgrades_legacy_rows_without_deleting_custom_catalogue(db):
    legacy_brand = Brand(name="Town Harvest", slug="town-harvest")
    legacy_category = Category(name="Fresh produce", slug="fresh-produce")
    custom_brand = Brand(name="Neighbourhood Brand", slug="neighbourhood-brand")
    custom_category = Category(name="Local favourites", slug="local-favourites")
    db.add_all([legacy_brand, legacy_category, custom_brand, custom_category])
    db.flush()
    tomatoes = Product(
        name="Tomatoes",
        slug="tomatoes",
        brand_id=legacy_brand.id,
        description="Old demo description",
        categories=[legacy_category],
    )
    custom = Product(
        name="Owner special",
        slug="owner-special",
        brand_id=custom_brand.id,
        categories=[custom_category],
    )
    db.add_all([tomatoes, custom])
    db.flush()
    obsolete = ProductVariant(
        product_id=tomatoes.id,
        name="Old pack",
        mrp="10",
        selling_price="9",
    )
    db.add(obsolete)
    db.commit()

    seed_catalogue(db)
    db.refresh(tomatoes)
    db.refresh(obsolete)

    assert tomatoes.brand.slug == "local-produce"
    assert tomatoes.description != "Old demo description"
    assert {category.slug for category in tomatoes.categories} == {"fresh-produce"}
    assert obsolete.active is False
    assert obsolete.available is False
    assert legacy_brand.active is False
    assert db.scalar(select(Product).where(Product.slug == "owner-special")) is custom


def test_seed_prices_respect_catalogue_invariants():
    for product in PRODUCTS:
        assert product.categories
        assert product.variants
        for variant in product.variants:
            assert variant.mrp >= 0
            assert 0 <= variant.selling_price <= variant.mrp
