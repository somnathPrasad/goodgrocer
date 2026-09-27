from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError

from app.api.routes import v1
from app.core.config import Settings
from app.models.domain import (
    Address,
    AuthSession,
    Customer,
    Favourite,
    Order,
    PaymentAttempt,
    now,
)
from app.schemas.domain import ProductInput, VariantInput
from app.services.auth import new_session


def cart(data, **changes):
    return {
        "items": [{"variant_id": data["variant"].id, "quantity": 2}],
        "fulfilment_type": "DELIVERY",
        "address_id": data["address"].id,
        "payment_method": "COD",
        **changes,
    }


def place(client, data, **changes):
    request = cart(data, **changes)
    quote = client.post("/api/v1/checkout/quote", json=request, headers=data["headers"])
    assert quote.status_code == 200, quote.text
    result = client.post(
        "/api/v1/orders",
        json={
            **request,
            "quote_token": quote.json()["quote_token"],
            "idempotency_key": "test-order-key-123456",
        },
        headers=data["headers"],
    )
    assert result.status_code == 201, result.text
    return result.json()


def owner(client, data):
    client.cookies.set("gg_admin", data["admin_token"])
    return {"Origin": "http://localhost:3000"}


def test_mobile_admin_session_and_browser_cookie_isolation(client, data):
    login = client.post(
        "/api/v1/admin/auth/mobile-login",
        json={"username": "owner", "password": "a-secure-test-password"},
    )
    assert login.status_code == 200, login.text
    assert "gg_admin" not in login.headers.get("set-cookie", "")
    headers = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/v1/admin/me", headers=headers).status_code == 200
    assert client.get("/api/v1/orders", headers=headers).status_code == 401
    assert (
        client.post(
            "/api/v1/admin/brands",
            json={"name": "Mobile", "slug": "mobile"},
            headers=headers,
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/admin/auth/mobile-login",
            json={"username": "owner", "password": "wrong"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/admin/auth/mobile-login",
            json={"username": "owner", "password": "a-secure-test-password"},
            headers={"Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert client.post("/api/v1/admin/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/admin/me", headers=headers).status_code == 401
    cookie_headers = owner(client, data)
    assert (
        client.post("/api/v1/admin/brands", json={"name": "Blocked", "slug": "blocked"}).status_code
        == 403
    )
    assert client.get("/api/v1/admin/me", headers=cookie_headers).status_code == 200


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


def test_catalogue_many_categories_search_and_pagination(client, data):
    for category in data["categories"]:
        response = client.get(f"/api/v1/products?category_id={category.id}&q=ric&page_size=1")
        assert response.status_code == 200, response.text
        assert response.json()["total"] == 1
        assert len(response.json()["items"][0]["categories"]) == 2
    assert client.get("/api/v1/products?page=2&page_size=1").json()["items"] == []
    assert client.get("/api/v1/products?q=absent").json()["total"] == 0


def test_inactive_product_is_hidden_from_catalogue(client, db, data):
    data["product"].active = False
    db.commit()
    assert client.get("/api/v1/products").json()["items"] == []


@pytest.mark.parametrize("mrp,price", [("-1", "0"), ("10", "-1"), ("10", "11"), ("10", "1.001")])
def test_price_validation(mrp, price):
    with pytest.raises(ValidationError):
        VariantInput(name="Test", mrp=mrp, selling_price=price)


def test_authentication_and_ownership_error_mapping(client, data):
    for path in ["/orders", "addresses", "favourites", "admin/products", "admin/orders"]:
        assert client.get("/api/v1/" + path.lstrip("/")).status_code == 401
    address = {
        "recipient_name": "Sam",
        "phone": "9876543210",
        "line1": "12 Market Road",
        "city": "Town",
        "state": "Karnataka",
    }
    created = client.post("/api/v1/addresses", json=address, headers=data["headers"])
    assert created.status_code == 201, created.text
    aid = created.json()["id"]
    assert created.json()["phone"] == "+919876543210"
    assert client.get("/api/v1/addresses", headers=data["other_headers"]).json() == []
    assert (
        client.put(
            f"/api/v1/addresses/{aid}", json=address, headers=data["other_headers"]
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/addresses/{aid}", headers=data["other_headers"]).status_code == 404
    )
    assert (
        client.post(
            "/api/v1/checkout/quote",
            json=cart(data, fulfilment_type="DELIVERY", address_id=aid),
            headers=data["other_headers"],
        ).status_code
        == 404
    )
    order = place(client, data, fulfilment_type="DELIVERY", address_id=aid)
    assert (
        client.get(f"/api/v1/orders/{order['id']}", headers=data["other_headers"]).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/orders/{order['id']}/reorder", headers=data["other_headers"]
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/addresses/{aid}", headers=data["headers"]).status_code == 204
    assert client.get(f"/api/v1/orders/{order['id']}", headers=data["headers"]).status_code == 200


def test_reverse_geocode_suggests_fields_for_confirmed_pin(client, data, monkeypatch):
    class GoogleResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "status": "OK",
                "results": [
                    {
                        "address_components": [
                            {"long_name": "Market Road", "types": ["route"]},
                            {"long_name": "Indiranagar", "types": ["sublocality_level_1"]},
                            {"long_name": "Bengaluru", "types": ["locality"]},
                            {"long_name": "Karnataka", "types": ["administrative_area_level_1"]},
                            {"long_name": "560038", "types": ["postal_code"]},
                        ]
                    }
                ],
            }

    monkeypatch.setattr(v1, "get_settings", lambda: Settings(google_geocoding_api_key="test-key"))
    monkeypatch.setattr(v1.httpx, "get", lambda *args, **kwargs: GoogleResponse())
    path = "/api/v1/addresses/reverse-geocode?latitude=12.9&longitude=77.6"
    assert client.get(path).status_code == 401
    result = client.get(path, headers=data["headers"])
    assert result.status_code == 200, result.text
    assert result.json() == {
        "line1": "Market Road",
        "locality": "Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
    }


def test_favourites_are_unique_and_owned(client, data):
    path = f"/api/v1/favourites/{data['product'].id}"
    assert client.put(path, headers=data["headers"]).status_code == 204
    assert client.put(path, headers=data["headers"]).status_code == 204
    assert len(client.get("/api/v1/favourites", headers=data["headers"]).json()) == 1
    assert client.get("/api/v1/favourites", headers=data["other_headers"]).json() == []
    client.delete(path, headers=data["other_headers"])
    assert len(client.get("/api/v1/favourites", headers=data["headers"]).json()) == 1


def test_google_sign_in_uses_verified_subject_and_logout(client, db, monkeypatch):
    monkeypatch.setattr(
        "app.services.auth.get_settings",
        lambda: Settings(google_web_client_id="web-client.apps.googleusercontent.com"),
    )

    def verify(token, request, audience):
        assert audience == "web-client.apps.googleusercontent.com"
        if token == "invalid":
            raise ValueError("bad signature")
        return {"sub": "google-account-123", "email": "person@example.com"}

    monkeypatch.setattr("app.services.auth.google_id_token.verify_oauth2_token", verify)
    assert client.post("/api/v1/auth/google", json={"id_token": "invalid"}).status_code == 401
    response = client.post("/api/v1/auth/google", json={"id_token": "valid"})
    assert response.status_code == 200, response.text
    customer = db.query(Customer).filter_by(google_subject="google-account-123").one()
    assert customer.phone_number is None
    again = client.post("/api/v1/auth/google", json={"id_token": "valid"})
    assert again.status_code == 200
    assert db.query(Customer).filter_by(google_subject="google-account-123").count() == 1
    headers = {"Authorization": "Bearer " + response.json()["token"]}
    assert client.get("/api/v1/orders", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/orders", headers=headers).status_code == 401


def test_customer_deletion_detaches_orders_and_erases_customer_data(client, db, data, monkeypatch):
    customer = Customer(google_subject="delete-google-subject")
    db.add(customer)
    db.flush()
    address = Address(
        customer_id=customer.id,
        recipient_name="Delete Me",
        phone="+919999999999",
        line1="Private road",
        city="Town",
        state="Karnataka",
    )
    db.add_all([address, Favourite(customer_id=customer.id, product_id=data["product"].id)])
    common = {
        "customer_id": customer.id,
        "customer_phone": "+919999999999",
        "request_hash": "1" * 64,
        "fulfilment_type": "DELIVERY",
        "payment_method": "COD",
        "subtotal": Decimal("100.25"),
        "delivery_fee": Decimal("0.00"),
        "discount": Decimal("0.00"),
        "total": Decimal("100.25"),
        "address_snapshot": {
            "recipient_name": "Delete Me",
            "phone": "+919999999999",
            "line1": "Private road",
            "city": "Town",
            "state": "Karnataka",
        },
    }
    active = Order(
        order_number="GG-DELETE-ACTIVE",
        idempotency_key="delete-active-order",
        **common,
    )
    expiring = Order(
        order_number="GG-DELETE-EXPIRING",
        idempotency_key="delete-expiring-order",
        **common,
    )
    terminal = Order(
        order_number="GG-DELETE-TERMINAL",
        idempotency_key="delete-terminal-order",
        status="DELIVERED",
        **common,
    )
    db.add_all([active, expiring, terminal])
    db.flush()
    db.add(
        PaymentAttempt(
            order_id=active.id,
            provider="development",
            reference="delete-this-attempt",
            amount=Decimal("100.25"),
        )
    )
    db.commit()
    session = new_session(db, customer_id=customer.id)

    monkeypatch.setattr(
        "app.services.auth.get_settings",
        lambda: Settings(google_web_client_id="web-client.apps.googleusercontent.com"),
    )
    monkeypatch.setattr(
        "app.services.auth.google_id_token.verify_oauth2_token",
        lambda token, request, audience: {
            "sub": "delete-google-subject",
            "email": "delete@example.com",
        },
    )
    headers = {"Authorization": "Bearer " + session["token"]}
    response = client.post(
        "/api/v1/account/deletion",
        json={"id_token": "fresh-delete-token"},
        headers=headers,
    )
    assert response.status_code == 204, response.text

    db.expire_all()
    assert db.get(Customer, customer.id) is None
    assert db.query(Address).filter_by(customer_id=customer.id).count() == 0
    assert db.query(Favourite).filter_by(customer_id=customer.id).count() == 0
    assert db.query(AuthSession).filter_by(customer_id=customer.id).count() == 0
    assert db.query(PaymentAttempt).filter_by(order_id=active.id).count() == 0
    active = db.get(Order, active.id)
    terminal = db.get(Order, terminal.id)
    assert active.customer_id is None and active.customer_deleted_at is not None
    assert active.customer_phone == "+919999999999" and active.address_snapshot is not None
    assert active.delivery_details_erase_at - active.customer_deleted_at == timedelta(days=30)
    assert terminal.customer_id is None and terminal.customer_phone is None
    assert terminal.address_snapshot is None
    assert client.get("/api/v1/orders", headers=headers).status_code == 401

    from app.services.customer_deletion import erase_expired_delivery_details

    assert erase_expired_delivery_details(db, expiring.delivery_details_erase_at) == 2
    db.refresh(active)
    db.refresh(expiring)
    assert active.customer_phone is None and active.address_snapshot is None
    assert expiring.customer_phone is None and expiring.address_snapshot is None

    # Repeating from the sessionless web path is intentionally successful.
    repeated = client.post("/api/v1/account/deletion", json={"id_token": "fresh-delete-token"})
    assert repeated.status_code == 204


def test_customer_deletion_rejects_different_google_account(client, db, monkeypatch):
    current = Customer(google_subject="current-google-subject")
    other = Customer(google_subject="other-google-subject")
    db.add_all([current, other])
    db.commit()
    session = new_session(db, customer_id=current.id)
    monkeypatch.setattr(
        "app.services.auth.get_settings",
        lambda: Settings(google_web_client_id="web-client.apps.googleusercontent.com"),
    )
    monkeypatch.setattr(
        "app.services.auth.google_id_token.verify_oauth2_token",
        lambda token, request, audience: {"sub": "other-google-subject"},
    )
    response = client.post(
        "/api/v1/account/deletion",
        json={"id_token": "other-token"},
        headers={"Authorization": "Bearer " + session["token"]},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "GOOGLE_ACCOUNT_MISMATCH"
    assert db.get(Customer, current.id) is not None
    assert db.get(Customer, other.id) is not None


def test_admin_csrf_auth_upload_and_product_edit(client, data):
    headers = owner(client, data)
    body = {
        "name": "New",
        "slug": "new",
        "brand_id": data["product"].brand_id,
        "category_ids": [c.id for c in data["categories"]],
    }
    assert client.post("/api/v1/admin/products", json=body).status_code == 403
    created = client.post("/api/v1/admin/products", json=body, headers=headers)
    assert created.status_code == 201, created.text
    assert len(created.json()["categories"]) == 2
    assert (
        client.post(
            "/api/v1/admin/images",
            files={"file": ("x.png", b"not an image", "image/png")},
            headers=headers,
        ).status_code
        == 400
    )
    image = BytesIO()
    Image.new("RGB", (10, 10)).save(image, format="PNG")
    uploaded = client.post(
        "/api/v1/admin/images",
        files={"file": ("x.png", image.getvalue(), "image/png")},
        headers=headers,
    )
    assert uploaded.status_code == 200, uploaded.text
    assert uploaded.json()["image_url"].endswith(".jpg")
    client.cookies.clear()
    assert (
        client.post(
            "/api/v1/admin/auth/login",
            json={"username": "owner", "password": "wrong"},
            headers=headers,
        ).status_code
        == 401
    )
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "owner", "password": "a-secure-test-password"},
        headers=headers,
    )
    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()
    assert client.get("/api/v1/admin/me").status_code == 200


def test_config_maps_first_release_checkout_capabilities(client):
    assert client.get("/api/v1/config").json()["online_upi_enabled"] is False


def test_production_rejects_development_providers():
    with pytest.raises(ValidationError):
        Settings(environment="production")


def test_supabase_storage_requires_current_backend_credentials():
    with pytest.raises(ValidationError, match="HTTPS SUPABASE_URL"):
        Settings(image_storage_provider="supabase", supabase_url=None, supabase_secret_key=None)
    with pytest.raises(ValidationError, match="current SUPABASE_SECRET_KEY"):
        Settings(
            image_storage_provider="supabase",
            supabase_url="https://example.supabase.co",
            supabase_secret_key="legacy-key",
        )


def test_production_accepts_supabase_storage_configuration():
    settings = Settings(
        environment="production",
        google_web_client_id="web-client.apps.googleusercontent.com",
        payment_provider="disabled",
        secret_key="a-production-secret-that-is-long-enough",
        public_api_url="https://api.example.com",
        admin_origin="https://admin.example.com",
        image_storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_secret_key="sb_secret_test",
    )

    assert settings.image_storage_provider == "supabase"


@pytest.mark.parametrize("quantity", [0, -1, 100])
def test_invalid_quantity(client, data, quantity):
    assert (
        client.post(
            "/api/v1/checkout/quote",
            json=cart(data, items=[{"variant_id": data["variant"].id, "quantity": quantity}]),
            headers=data["headers"],
        ).status_code
        == 422
    )


def test_session_expiry_and_admin_customer_separation(client, db, data):
    from app.models.domain import AuthSession
    from app.services.auth import digest

    token = data["headers"]["Authorization"].removeprefix("Bearer ")
    row = db.get(AuthSession, digest(token))
    row.expires_at = now() - timedelta(seconds=1)
    db.commit()
    assert client.get("/api/v1/orders", headers=data["headers"]).status_code == 401
    assert (
        client.get(
            "/api/v1/orders", headers={"Authorization": "Bearer " + data["admin_token"]}
        ).status_code
        == 401
    )
    client.cookies.set("gg_admin", data["other_headers"]["Authorization"].removeprefix("Bearer "))
    assert client.get("/api/v1/admin/me").status_code == 401


def test_category_reorder_variant_deactivation_and_price_validation(client, data):
    headers = owner(client, data)
    category = data["categories"][0]
    updated = client.put(
        f"/api/v1/admin/categories/{category.id}",
        json={"name": "Fresh edited", "slug": "fresh", "display_order": 99, "active": True},
        headers=headers,
    )
    assert updated.status_code == 200
    assert client.get("/api/v1/categories").json()[-1]["id"] == category.id
    path = f"/api/v1/admin/products/{data['product'].id}/variants/{data['variant'].id}"
    assert (
        client.put(
            path, json={"name": "1 kg", "mrp": "100", "selling_price": "101"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.put(
            path,
            json={"name": "1 kg", "mrp": "100", "selling_price": "99", "active": False},
            headers=headers,
        ).status_code
        == 200
    )
    assert client.get(f"/api/v1/products/{data['product'].id}").json()["variants"] == []


def test_catalogue_query_count_does_not_grow_per_product(client, db, data):
    from sqlalchemy import event

    from app.models.domain import Product, ProductVariant

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
                product_id=product.id, name="Regular", mrp=Decimal("10"), selling_price=Decimal("9")
            )
        )
    db.commit()
    db.expire_all()
    statements = []

    def record(connection, cursor, statement, parameters, context, many):
        statements.append(statement)

    event.listen(db.bind, "before_cursor_execute", record)
    try:
        response = client.get("/api/v1/products?page_size=24")
        assert response.status_code == 200
        assert response.json()["total"] == 13
        assert len(statements) <= 6
    finally:
        event.remove(db.bind, "before_cursor_execute", record)
