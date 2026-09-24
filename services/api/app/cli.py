import argparse
import getpass
import json
import shutil
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.domain import Admin, Brand, Category, Product, ProductVariant
from app.seed_data import (
    BRANDS,
    CATEGORIES,
    LEGACY_SEED_BRANDS,
    LEGACY_SEED_CATEGORIES,
    PRODUCTS,
)
from app.services.auth import password_hasher


def seed_images(db):
    assets = Path(__file__).resolve().parents[1] / "seed-assets"
    media = get_settings().media_dir
    media.mkdir(parents=True, exist_ok=True)
    image_products = {
        "tomatoes.jpg": ("tomatoes",),
        "bananas.jpg": ("bananas",),
        "potatoes.jpg": ("potatoes",),
        "onions.jpg": ("onions",),
        "fresh-milk.jpg": ("fresh-milk",),
        "sona-masoori-rice.jpg": ("sona-masoori-rice",),
        "whole-wheat-atta.jpg": ("whole-wheat-atta",),
        "toor-dal.jpg": ("toor-dal",),
        "sunflower-oil.jpg": ("sunflower-oil",),
        "spices.jpg": (
            "everest-turmeric-powder",
            "everest-red-chilli-powder",
            "everest-coriander-powder",
        ),
        "tea.jpg": ("tea",),
    }
    media_urls = {}
    for filename, product_slugs in image_products.items():
        target = media / f"demo-{filename}"
        if not target.exists():
            shutil.copyfile(assets / filename, target)
        media_url = f"/media/{target.name}"
        media_urls[filename] = media_url
        for slug in product_slugs:
            product = db.scalar(select(Product).where(Product.slug == slug))
            if product and not product.image_url:
                product.image_url = media_url

    category_images = {
        "fresh-produce": "tomatoes.jpg",
        "dairy-breakfast": "fresh-milk.jpg",
        "rice-grains": "sona-masoori-rice.jpg",
        "dals-pulses": "toor-dal.jpg",
        "oil-ghee": "sunflower-oil.jpg",
        "masala-essentials": "spices.jpg",
        "tea-beverages": "tea.jpg",
    }
    for slug, filename in category_images.items():
        category = db.scalar(select(Category).where(Category.slug == slug))
        if category and not category.image_url:
            category.image_url = media_urls[filename]
    db.commit()


def seed():
    if get_settings().environment == "production":
        raise SystemExit("Development seed is forbidden in production")
    with SessionLocal() as db:
        counts = seed_catalogue(db)
        seed_images(db)
        print(
            "Seeded or refreshed "
            f"{counts['brands']} brands, {counts['categories']} categories, "
            f"{counts['products']} products and {counts['variants']} variants. "
            "Representative development data only; prices are not live."
        )


def seed_catalogue(db):
    """Upsert only known seed records, preserving unrelated local catalogue data."""
    brands = {brand.slug: brand for brand in db.scalars(select(Brand)).all()}
    for name, slug in BRANDS:
        brand = brands.get(slug)
        if brand is None:
            brand = Brand(slug=slug)
            brands[slug] = brand
            db.add(brand)
        brand.name = name
        brand.active = True
    for slug in LEGACY_SEED_BRANDS:
        if brand := brands.get(slug):
            brand.active = False

    categories = {category.slug: category for category in db.scalars(select(Category)).all()}
    for display_order, (name, slug) in enumerate(CATEGORIES):
        category = categories.get(slug)
        if category is None:
            category = Category(slug=slug)
            categories[slug] = category
            db.add(category)
        category.name = name
        category.display_order = display_order
        category.active = True
    for slug in LEGACY_SEED_CATEGORIES:
        if category := categories.get(slug):
            category.active = False
    db.flush()

    products = {product.slug: product for product in db.scalars(select(Product)).all()}
    variant_count = 0
    for row in PRODUCTS:
        product = products.get(row.slug)
        if product is None:
            product = Product(slug=row.slug)
            products[row.slug] = product
            db.add(product)
        product.name = row.name
        product.brand_id = brands[row.brand].id
        product.description = row.description
        product.categories = [categories[slug] for slug in row.categories]
        product.active = True
        product.available = row.available
        db.flush()

        existing = {variant.name: variant for variant in product.variants}
        current_names = {variant.name for variant in row.variants}
        for old_name, old_variant in existing.items():
            if old_name not in current_names:
                # Keep rows that old demo orders may reference, but hide them.
                old_variant.active = False
                old_variant.available = False
        for display_order, row_variant in enumerate(row.variants):
            variant = existing.get(row_variant.name)
            if variant is None:
                variant = ProductVariant(product_id=product.id, name=row_variant.name)
                db.add(variant)
            variant.mrp = row_variant.mrp
            variant.selling_price = row_variant.selling_price
            variant.display_order = display_order
            variant.active = True
            variant.available = row_variant.available
            variant_count += 1

    db.commit()
    return {
        "brands": len(BRANDS),
        "categories": len(CATEGORIES),
        "products": len(PRODUCTS),
        "variants": variant_count,
    }


def bootstrap():
    username = input("Admin username: ").strip()
    password = getpass.getpass("Password (at least 12 characters): ")
    if not username or len(username) > 100 or len(password) < 12 or len(password) > 200:
        raise SystemExit("Invalid username or password length")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match")
    with SessionLocal() as db:
        if db.scalar(select(Admin).where(Admin.username == username)):
            raise SystemExit("Account exists; refusing to overwrite")
        db.add(Admin(username=username, password_hash=password_hasher.hash(password)))
        db.commit()
        print("Admin created.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=[
            "seed",
            "bootstrap-admin",
            "export-openapi",
            "erase-expired-customer-data",
        ],
    )
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.command == "bootstrap-admin":
        bootstrap()
    elif args.command == "erase-expired-customer-data":
        from app.services.customer_deletion import erase_expired_delivery_details

        with SessionLocal() as db:
            count = erase_expired_delivery_details(db)
        print(f"Erased delivery details from {count} retained order(s).")
    else:
        from app.main import app

        path = Path(__file__).resolve().parents[3] / "packages/api-contracts/openapi.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(app.openapi(), indent=2) + "\n")
        print(path)


if __name__ == "__main__":
    main()
