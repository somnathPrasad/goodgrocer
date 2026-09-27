from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import DomainError
from app.services.auth import rate_limit

_GOOGLE_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"
_LOOKUP_FAILED = "Address lookup failed. Enter the address manually."


def _lookup_failed():
    return DomainError("ADDRESS_LOOKUP_FAILED", _LOOKUP_FAILED, 502)


def _request_google(latitude: Decimal, longitude: Decimal, api_key: str):
    return httpx.get(
        _GOOGLE_GEOCODING_URL,
        params={
            "latlng": f"{latitude},{longitude}",
            "key": api_key,
            "language": "en",
            "region": "in",
        },
        timeout=5,
    )


def suggest_address(
    db: Session,
    customer_id: int,
    latitude: Decimal,
    longitude: Decimal,
):
    key = get_settings().google_geocoding_api_key
    if key is None:
        raise DomainError("MAPS_NOT_CONFIGURED", "Address lookup is unavailable.", 503)

    rate_limit(db, f"geocode-customer:{customer_id}", 100, 86400)
    try:
        response = _request_google(latitude, longitude, key.get_secret_value())
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise _lookup_failed() from exc

    if not isinstance(payload, dict):
        raise _lookup_failed()
    if payload.get("status") == "ZERO_RESULTS":
        return {"line1": "", "locality": "", "city": "", "state": "", "postal_code": ""}
    results = payload.get("results")
    if (
        payload.get("status") != "OK"
        or not isinstance(results, list)
        or not results
        or not isinstance(results[0], dict)
    ):
        raise _lookup_failed()

    components = results[0].get("address_components", [])
    if not isinstance(components, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("types", []), list)
        or not isinstance(item.get("long_name", ""), str)
        for item in components
    ):
        raise _lookup_failed()

    def component(*types: str) -> str:
        for kind in types:
            for item in components:
                if kind in item.get("types", []):
                    return item.get("long_name", "")
        return ""

    return {
        "line1": " ".join(filter(None, [component("street_number"), component("route")])),
        "locality": component("sublocality_level_1", "sublocality", "neighborhood"),
        "city": component("locality", "administrative_area_level_3", "administrative_area_level_2"),
        "state": component("administrative_area_level_1"),
        "postal_code": component("postal_code"),
    }
