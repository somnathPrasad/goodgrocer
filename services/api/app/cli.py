import argparse
import getpass
import json
import shutil
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.domain import Admin, Brand, Category, Product, ProductVariant
from app.services.auth import password_hasher


def seed_images(db):
    assets = Path(__file__).resolve().parents[1] / "seed-assets"
    media = get_settings().media_dir
    media.mkdir(parents=True, exist_ok=True)
    for slug in ("tomatoes", "bananas"):
        product = db.scalar(
            select(Product).join(Brand).where(Product.slug == slug, Brand.slug == "town-harvest")
        )
        if product and not product.image_url:
            shutil.copyfile(assets / f"{slug}.jpg", media / f"demo-{slug}.jpg")
            product.image_url = f"/media/demo-{slug}.jpg"
    category = db.scalar(select(Category).where(Category.slug == "fresh-produce"))
    if category and not category.image_url and (media / "demo-tomatoes.jpg").exists():
        category.image_url = "/media/demo-tomatoes.jpg"
    db.commit()


def seed():
    if get_settings().environment == "production":
        raise SystemExit("Development seed is forbidden in production")
    with SessionLocal() as db:
        if db.scalar(select(Product.id).limit(1)):
            seed_images(db)
            print("Catalogue already contains products; only missing demo photos were added.")
            return
        brands = [
            Brand(name=n, slug=s)
            for n, s in [
                ("Town Harvest", "town-harvest"),
                ("Daily Dairy", "daily-dairy"),
                ("Pantry & Co", "pantry-co"),
            ]
        ]
        categories = [
            Category(name=n, slug=s, display_order=i)
            for i, (n, s) in enumerate(
                [
                    ("Fresh produce", "fresh-produce"),
                    ("Dairy & breakfast", "dairy-breakfast"),
                    ("Rice & grains", "rice-grains"),
                    ("Pantry essentials", "pantry-essentials"),
                    ("Snacks & drinks", "snacks-drinks"),
                ]
            )
        ]
        db.add_all(brands + categories)
        db.flush()
        rows = [
            ("Tomatoes", 0, [0], [("500 g", "30", "24"), ("1 kg", "60", "45")]),
            ("Bananas", 0, [0, 1], [("Pack of 6", "50", "45")]),
            ("Potatoes", 0, [0], [("1 kg", "40", "40")]),
            ("Onions", 0, [0, 3], [("1 kg", "45", "39")]),
            ("Fresh milk", 1, [1], [("500 ml", "30", "30"), ("1 L", "60", "58")]),
            ("Natural curd", 1, [1], [("400 g", "45", "40")]),
            ("Paneer", 1, [1], [("200 g", "100", "90")]),
            (
                "Basmati rice",
                2,
                [2, 3],
                [("1 kg", "160", "145"), ("5 kg", "780", "700")],
            ),
            (
                "Whole wheat atta",
                2,
                [2, 3],
                [("1 kg", "60", "55"), ("5 kg", "290", "260")],
            ),
            ("Toor dal", 2, [2, 3], [("500 g", "90", "85"), ("1 kg", "180", "165")]),
            ("Sunflower oil", 2, [3], [("1 L", "160", "145"), ("2 L", "320", "280")]),
            ("Tea", 2, [1, 4], [("250 g", "150", "135")]),
            ("Salt", 2, [3], [("1 kg", "28", "28")]),
            (
                "Roasted peanuts",
                2,
                [4],
                [("Regular", "45", "40"), ("Family Pack", "100", "85")],
            ),
            ("Biscuits", 2, [1, 4], [("Pack of 6", "60", "55")]),
            ("Mango juice", 2, [4], [("1 L", "110", "99")]),
        ]
        for i, (name, brand, cats, variants) in enumerate(rows):
            product = Product(
                name=name,
                slug=name.lower().replace(" ", "-"),
                brand_id=brands[brand].id,
                description=f"{name} for your everyday kitchen. Selected by your neighbourhood store.",
                categories=[categories[c] for c in cats],
                available=i != 6,
            )
            db.add(product)
            db.flush()
            for j, (label, mrp, price) in enumerate(variants):
                db.add(
                    ProductVariant(
                        product_id=product.id,
                        name=label,
                        mrp=mrp,
                        selling_price=price,
                        display_order=j,
                        available=not (i == 7 and j == 1),
                    )
                )
        db.commit()
        seed_images(db)
        print("Seeded 3 brands, 5 categories and 16 products. Demo data only.")


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
    parser.add_argument("command", choices=["seed", "bootstrap-admin", "export-openapi"])
    args = parser.parse_args()
    if args.command == "seed":
        seed()
    elif args.command == "bootstrap-admin":
        bootstrap()
    else:
        from app.main import app

        path = Path(__file__).resolve().parents[3] / "packages/api-contracts/openapi.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(app.openapi(), indent=2) + "\n")
        print(path)


if __name__ == "__main__":
    main()
