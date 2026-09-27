import pytest


def cart(data, quantity):
    return {
        "items": [{"variant_id": data["variant"].id, "quantity": quantity}],
        "fulfilment_type": "DELIVERY",
        "address_id": data["address"].id,
        "payment_method": "COD",
    }


@pytest.mark.parametrize("quantity", [0, -1, 100])
def test_checkout_rejects_invalid_quantity_at_transport(client, data, quantity):
    response = client.post(
        "/api/v1/checkout/quote",
        json=cart(data, quantity),
        headers=data["headers"],
    )
    assert response.status_code == 422


@pytest.mark.parametrize("path", ["orders", "addresses", "favourites"])
def test_customer_adapters_require_authentication(client, path):
    assert client.get("/api/v1/" + path).status_code == 401


@pytest.mark.parametrize("path", ["admin/products", "admin/orders"])
def test_owner_adapters_require_authentication(client, path):
    assert client.get("/api/v1/" + path).status_code == 401
