import os
from decimal import Decimal
from uuid import uuid4

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://goodgrocer:goodgrocer@localhost:5432/goodgrocer"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app
from app.models.domain import Admin, Brand, Category, Customer, Product, ProductVariant
from app.services.auth import new_session, password_hasher


@pytest.fixture()
def db():
    # Each test has a unique PostgreSQL schema: never drop/truncate application data.
    engine = create_engine(os.environ.get("TEST_DATABASE_URL", str(get_settings().database_url)))
    schema = "test_" + uuid4().hex
    with engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    isolated = engine.execution_options(schema_translate_map={None: schema})
    Base.metadata.create_all(isolated)
    with Session(isolated, expire_on_commit=False) as session:
        yield session
    with engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    engine.dispose()


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def data(db):
    brand = Brand(name="Farm", slug="farm")
    categories = [Category(name="Fresh", slug="fresh"), Category(name="Daily", slug="daily")]
    customer = Customer(phone_number="+919876543210")
    other = Customer(phone_number="+919876543211")
    admin = Admin(username="owner", password_hash=password_hasher.hash("a-secure-test-password"))
    db.add_all([brand, *categories, customer, other, admin])
    db.flush()
    product = Product(name="Rice", slug="rice", brand_id=brand.id, categories=categories)
    db.add(product)
    db.flush()
    variant = ProductVariant(
        product_id=product.id, name="1 kg", mrp=Decimal("120.00"), selling_price=Decimal("100.25")
    )
    db.add(variant)
    db.commit()
    token = new_session(db, customer_id=customer.id)["token"]
    other_token = new_session(db, customer_id=other.id)["token"]
    admin_token = new_session(db, admin_id=admin.id)["token"]
    return {
        "product": product,
        "variant": variant,
        "customer": customer,
        "categories": categories,
        "headers": {"Authorization": f"Bearer {token}"},
        "other_headers": {"Authorization": f"Bearer {other_token}"},
        "admin_token": admin_token,
    }
