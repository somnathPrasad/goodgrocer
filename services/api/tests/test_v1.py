from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError

from app.api.routes import v1
from app.core.config import Settings
from app.models.domain import Address, Customer, Order, OrderItem, PaymentAttempt, now
from app.schemas.domain import ProductInput, VariantInput


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


def legacy_order(db, data, fulfilment_type, payment_method):
    order = Order(
        order_number=f"GG-LEGACY-{fulfilment_type}-{payment_method}",
        customer_id=data["customer"].id,
        customer_phone="+919876543210",
        idempotency_key=f"legacy-{fulfilment_type}-{payment_method}",
        request_hash="0" * 64,
        fulfilment_type=fulfilment_type,
        payment_method=payment_method,
        subtotal=Decimal("100.25"),
        delivery_fee=Decimal("0.00"),
        discount=Decimal("0.00"),
        total=Decimal("100.25"),
        address_snapshot=None,
    )
    order.items = [
        OrderItem(
            product_id=data["product"].id,
            variant_id=data["variant"].id,
            product_name="Rice",
            variant_name="1 kg",
            quantity=1,
            unit_mrp=Decimal("120.00"),
            unit_selling_price=Decimal("100.25"),
            line_total=Decimal("100.25"),
        )
    ]
    if payment_method == "ONLINE_UPI":
        order.payment_attempts = [
            PaymentAttempt(
                provider="development",
                reference="legacy-payment-reference",
                amount=Decimal("100.25"),
            )
        ]
    db.add(order)
    db.commit()
    return order


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


@pytest.mark.parametrize(
    "field,model",
    [
        ("active", "product"),
        ("available", "product"),
        ("active", "variant"),
        ("available", "variant"),
    ],
)
def test_availability_enforced(client, db, data, field, model):
    setattr(data[model], field, False)
    db.commit()
    response = client.post("/api/v1/checkout/quote", json=cart(data), headers=data["headers"])
    assert response.status_code == 409
    if field == "active" and model == "product":
        assert client.get("/api/v1/products").json()["items"] == []


@pytest.mark.parametrize("mrp,price", [("-1", "0"), ("10", "-1"), ("10", "11"), ("10", "1.001")])
def test_price_validation(mrp, price):
    with pytest.raises(ValidationError):
        VariantInput(name="Test", mrp=mrp, selling_price=price)


def test_order_totals_snapshot_idempotency_and_stale(client, db, data):
    request = cart(data)
    quote = client.post("/api/v1/checkout/quote", json=request, headers=data["headers"]).json()
    assert quote["total"] == "200.50"
    payload = {
        **request,
        "quote_token": quote["quote_token"],
        "idempotency_key": "stable-request-key-123",
    }
    first = client.post("/api/v1/orders", json=payload, headers=data["headers"])
    assert first.status_code == 201, first.text
    assert (
        client.post("/api/v1/orders", json=payload, headers=data["headers"]).json()["id"]
        == first.json()["id"]
    )
    data["variant"].selling_price = Decimal("110.00")
    data["product"].name = "New rice name"
    db.commit()
    assert (
        client.get(f"/api/v1/orders/{first.json()['id']}", headers=data["headers"]).json()["items"][
            0
        ]["product_name"]
        == "Rice"
    )
    assert (
        client.post(
            "/api/v1/orders",
            json={**payload, "idempotency_key": "another-request-12345"},
            headers=data["headers"],
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/api/v1/orders",
            json={**payload, "items": [{"variant_id": data["variant"].id, "quantity": 3}]},
            headers=data["headers"],
        ).status_code
        == 409
    )


def test_auth_and_ownership(client, data):
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
    assert order["address_snapshot"]["line1"] == "12 Market Road"
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
    assert (
        client.get(f"/api/v1/orders/{order['id']}", headers=data["headers"]).json()[
            "address_snapshot"
        ]["line1"]
        == "12 Market Road"
    )


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


def test_status_transitions_and_terminal(client, data):
    order = place(client, data)
    headers = owner(client, data)
    path = f"/api/v1/admin/orders/{order['id']}/status"
    assert client.post(path, json={"status": "DELIVERED"}, headers=headers).status_code == 409
    assert client.post(path, json={"status": "ACCEPTED"}, headers=headers).status_code == 200
    assert (
        client.post(path, json={"status": "OUT_FOR_DELIVERY"}, headers=headers).status_code == 200
    )
    assert client.post(path, json={"status": "DELIVERED"}, headers=headers).status_code == 200
    assert (
        client.post(
            path, json={"status": "CANCELLED", "reason": "late"}, headers=headers
        ).status_code
        == 409
    )


def test_cancel_reason_and_terminal(client, data):
    order = place(client, data)
    headers = owner(client, data)
    path = f"/api/v1/admin/orders/{order['id']}/status"
    assert client.post(path, json={"status": "CANCELLED"}, headers=headers).status_code == 400
    assert (
        client.post(
            path, json={"status": "CANCELLED", "reason": "Cannot serve address"}, headers=headers
        ).status_code
        == 200
    )
    assert client.post(path, json={"status": "ACCEPTED"}, headers=headers).status_code == 409


def test_reorder_current_price_and_unavailable(client, db, data):
    order = place(client, data)
    data["variant"].selling_price = Decimal("90.00")
    db.commit()
    path = f"/api/v1/orders/{order['id']}/reorder"
    result = client.post(path, headers=data["headers"]).json()
    assert result["products"][0]["variants"][0]["selling_price"] == "90.00"
    data["variant"].available = False
    db.commit()
    result = client.post(path, headers=data["headers"]).json()
    assert result["items"] == [] and result["unavailable"] == ["Rice · 1 kg"]


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


def test_google_customer_pickup_is_unavailable(client, db, data):
    google_customer = Customer(google_subject="google-account-456")
    db.add(google_customer)
    db.commit()
    from app.services.auth import new_session

    headers = {
        "Authorization": "Bearer " + new_session(db, customer_id=google_customer.id)["token"]
    }
    request = cart(data, fulfilment_type="PICKUP", contact_phone="9876543210")
    quote = client.post("/api/v1/checkout/quote", json=request, headers=headers)
    assert quote.status_code == 422
    assert quote.json()["error"]["code"] == "FULFILMENT_UNAVAILABLE"


def test_pickup_order_cannot_use_an_existing_delivery_quote(client, data):
    quote = client.post("/api/v1/checkout/quote", json=cart(data), headers=data["headers"]).json()
    order = client.post(
        "/api/v1/orders",
        json={
            **cart(data, fulfilment_type="PICKUP"),
            "quote_token": quote["quote_token"],
            "idempotency_key": "disabled-pickup-key-123",
        },
        headers=data["headers"],
    )
    assert order.status_code == 422
    assert order.json()["error"]["code"] == "FULFILMENT_UNAVAILABLE"


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


@pytest.mark.parametrize("payment_method", ["UPI_ON_DELIVERY", "ONLINE_UPI"])
def test_non_cash_payment_is_unavailable_for_new_orders(client, data, payment_method):
    assert client.get("/api/v1/config").json()["online_upi_enabled"] is False
    request = cart(data, payment_method=payment_method)
    quote = client.post("/api/v1/checkout/quote", json=request, headers=data["headers"])
    assert quote.status_code == 422
    assert quote.json()["error"]["code"] == "PAYMENT_METHOD_UNAVAILABLE"

    cod_quote = client.post(
        "/api/v1/checkout/quote", json=cart(data), headers=data["headers"]
    ).json()
    order = client.post(
        "/api/v1/orders",
        json={
            **request,
            "quote_token": cod_quote["quote_token"],
            "idempotency_key": "disabled-payment-key-123",
        },
        headers=data["headers"],
    )
    assert order.status_code == 422
    assert order.json()["error"]["code"] == "PAYMENT_METHOD_UNAVAILABLE"


def test_existing_pickup_order_can_be_completed(client, db, data):
    order = legacy_order(db, data, "PICKUP", "UPI_ON_DELIVERY")
    customer_path = f"/api/v1/orders/{order.id}"
    assert client.get(customer_path, headers=data["headers"]).json()["fulfilment_type"] == "PICKUP"
    headers = owner(client, data)
    owner_path = f"/api/v1/admin/orders/{order.id}"
    assert (
        client.post(
            owner_path + "/status", json={"status": "ACCEPTED"}, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            owner_path + "/status", json={"status": "DELIVERED"}, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(owner_path + "/mark-paid", headers=headers).json()["payment_status"] == "PAID"
    )


def test_existing_online_order_can_complete_payment(client, db, data):
    order = legacy_order(db, data, "DELIVERY", "ONLINE_UPI")
    headers = owner(client, data)
    path = f"/api/v1/admin/orders/{order.id}/status"
    assert client.post(path, json={"status": "ACCEPTED"}, headers=headers).status_code == 409
    payment_path = f"/api/v1/orders/{order.id}/development-payment?outcome=PAID"
    assert client.post(payment_path, headers=data["other_headers"]).status_code == 404
    assert client.post(payment_path, headers=data["headers"]).status_code == 200
    assert client.post(path, json={"status": "ACCEPTED"}, headers=headers).status_code == 200


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


def test_delivery_full_lifecycle_and_payment_received(client, data):
    address = client.post(
        "/api/v1/addresses",
        json={
            "recipient_name": "Sam",
            "phone": "9876543210",
            "line1": "Market road",
            "city": "Town",
            "state": "Karnataka",
        },
        headers=data["headers"],
    ).json()
    order = place(
        client,
        data,
        fulfilment_type="DELIVERY",
        address_id=address["id"],
    )
    headers = owner(client, data)
    path = f"/api/v1/admin/orders/{order['id']}"
    for status in ["ACCEPTED", "OUT_FOR_DELIVERY", "DELIVERED"]:
        response = client.post(path + "/status", json={"status": status}, headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["payment_status"] == "PENDING"
    assert client.post(path + "/mark-paid", headers=headers).json()["payment_status"] == "PAID"
    assert (
        client.get(f"/api/v1/orders/{order['id']}", headers=data["headers"]).json()["status"]
        == "DELIVERED"
    )


def test_quote_tampering_and_customer_binding(client, db, data):
    request = cart(data)
    quote = client.post("/api/v1/checkout/quote", json=request, headers=data["headers"]).json()
    other_customer = db.query(Customer).filter_by(phone_number="+919876543211").one()
    other_address = Address(
        customer_id=other_customer.id,
        recipient_name="Other customer",
        phone="+919876543211",
        line1="Other road",
        city="Town",
        state="Karnataka",
    )
    db.add(other_address)
    db.commit()
    payload = {
        **request,
        "quote_token": quote["quote_token"],
        "idempotency_key": "test-bound-quote-1234",
    }
    assert (
        client.post(
            "/api/v1/orders",
            json={**payload, "address_id": other_address.id},
            headers=data["other_headers"],
        ).status_code
        == 409
    )
    payload["quote_token"] = "tampered." + quote["quote_token"]
    assert client.post("/api/v1/orders", json=payload, headers=data["headers"]).status_code == 409


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
