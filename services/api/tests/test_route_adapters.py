import json
from pathlib import Path

from app.main import app


def endpoint_modules(router):
    for route in router.routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from endpoint_modules(included)
        elif getattr(route, "path", "").startswith("/api/v1"):
            yield route.endpoint.__module__


def test_v1_contract_matches_exported_openapi():
    contract_path = Path(__file__).resolve().parents[3] / "packages/api-contracts/openapi.json"

    assert app.openapi() == json.loads(contract_path.read_text())


def test_v1_endpoints_are_owned_by_domain_oriented_adapters():
    adapter_modules = set(endpoint_modules(app.router))

    assert adapter_modules == {
        "app.api.routes.addresses",
        "app.api.routes.admin_auth",
        "app.api.routes.admin_catalogue",
        "app.api.routes.admin_dashboard",
        "app.api.routes.admin_orders",
        "app.api.routes.catalogue",
        "app.api.routes.configuration",
        "app.api.routes.customer_auth",
        "app.api.routes.favourites",
        "app.api.routes.images",
        "app.api.routes.orders",
        "app.api.routes.whatsapp_webhooks",
    }
