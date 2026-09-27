import pytest

from app.core.errors import DomainError
from app.schemas.domain import AddressInput
from app.services import customer_data


def address_input(**changes):
    return AddressInput.model_validate(
        {
            "recipient_name": "Customer",
            "phone": "+919876543210",
            "line1": "New market road",
            "city": "Town",
            "state": "Karnataka",
            **changes,
        }
    )


def test_saved_address_workflow_is_customer_scoped(db, data):
    created = customer_data.create_address(db, data["customer"].id, address_input())
    assert customer_data.list_addresses(db, data["customer"].id)[-1] == created

    updated = customer_data.update_address(
        db,
        data["customer"].id,
        created.id,
        address_input(line1="Updated market road"),
    )
    assert updated.line1 == "Updated market road"

    with pytest.raises(DomainError) as error:
        customer_data.update_address(db, 999_999, created.id, address_input())
    assert (error.value.code, error.value.status) == ("NOT_FOUND", 404)

    customer_data.delete_address(db, data["customer"].id, created.id)
    assert created not in customer_data.list_addresses(db, data["customer"].id)


def test_account_favourites_are_unique_and_customer_scoped(db, data):
    customer_data.add_favourite(db, data["customer"].id, data["product"].id)
    customer_data.add_favourite(db, data["customer"].id, data["product"].id)

    assert [product.id for product in customer_data.list_favourites(db, data["customer"].id)] == [
        data["product"].id
    ]

    customer_data.remove_favourite(db, data["customer"].id, data["product"].id)
    assert customer_data.list_favourites(db, data["customer"].id) == []
