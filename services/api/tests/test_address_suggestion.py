from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import DomainError
from app.services import address_suggestion


class GoogleResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def configure_google(monkeypatch, payload):
    monkeypatch.setattr(
        address_suggestion,
        "get_settings",
        lambda: Settings(google_geocoding_api_key="test-key"),
    )
    monkeypatch.setattr(
        address_suggestion,
        "_request_google",
        lambda *args: GoogleResponse(payload),
    )


def test_suggest_address_extracts_customer_editable_fields(db, data, monkeypatch):
    configure_google(
        monkeypatch,
        {
            "status": "OK",
            "results": [
                {
                    "address_components": [
                        {"long_name": "12", "types": ["street_number"]},
                        {"long_name": "Market Road", "types": ["route"]},
                        {"long_name": "Indiranagar", "types": ["sublocality_level_1"]},
                        {"long_name": "Bengaluru", "types": ["locality"]},
                        {
                            "long_name": "Karnataka",
                            "types": ["administrative_area_level_1"],
                        },
                        {"long_name": "560038", "types": ["postal_code"]},
                    ]
                }
            ],
        },
    )

    result = address_suggestion.suggest_address(
        db,
        data["customer"].id,
        Decimal("12.9"),
        Decimal("77.6"),
    )

    assert result == {
        "line1": "12 Market Road",
        "locality": "Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
    }


def test_suggest_address_returns_empty_fields_for_zero_results(db, data, monkeypatch):
    configure_google(monkeypatch, {"status": "ZERO_RESULTS", "results": []})

    result = address_suggestion.suggest_address(
        db, data["customer"].id, Decimal("12.9"), Decimal("77.6")
    )

    assert result == {"line1": "", "locality": "", "city": "", "state": "", "postal_code": ""}


@pytest.mark.parametrize(
    "payload",
    [
        ["not", "an", "object"],
        {"status": "OK", "results": [None]},
        {"status": "OK", "results": [{"address_components": None}]},
    ],
)
def test_suggest_address_translates_malformed_provider_response(db, data, monkeypatch, payload):
    configure_google(monkeypatch, payload)

    with pytest.raises(DomainError) as error:
        address_suggestion.suggest_address(
            db, data["customer"].id, Decimal("12.9"), Decimal("77.6")
        )

    assert (error.value.code, error.value.status, error.value.message) == (
        "ADDRESS_LOOKUP_FAILED",
        502,
        "Address lookup failed. Enter the address manually.",
    )


def test_suggest_address_translates_provider_failure(db, data, monkeypatch):
    configure_google(monkeypatch, {})

    def fail(*args):
        raise httpx.ConnectError("Google unavailable")

    monkeypatch.setattr(address_suggestion, "_request_google", fail)

    with pytest.raises(DomainError) as error:
        address_suggestion.suggest_address(
            db, data["customer"].id, Decimal("12.9"), Decimal("77.6")
        )

    assert (error.value.code, error.value.status) == ("ADDRESS_LOOKUP_FAILED", 502)


def test_suggest_address_reports_missing_configuration(db, data, monkeypatch):
    monkeypatch.setattr(
        address_suggestion,
        "get_settings",
        lambda: Settings(google_geocoding_api_key=None),
    )

    with pytest.raises(DomainError) as error:
        address_suggestion.suggest_address(
            db, data["customer"].id, Decimal("12.9"), Decimal("77.6")
        )

    assert (error.value.code, error.value.status) == ("MAPS_NOT_CONFIGURED", 503)
