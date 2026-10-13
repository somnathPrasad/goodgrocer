from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy.orm import Session

from app.models.domain import AuthSession, Customer
from app.services import customer_data
from app.services.auth import digest, new_session

PATH = "/api/v1/account/address-onboarding"


def test_eligibility_read_does_not_consume_address_offer(client, data):
    headers = data["other_headers"]
    assert client.get(PATH, headers=headers).json() == {"eligible": True}
    assert client.get(PATH, headers=headers).json() == {"eligible": True}


def test_claim_is_shared_across_sessions_and_survives_address_deletion(client, db, data):
    headers = data["other_headers"]
    assert client.post(PATH, headers=headers).json() == {"eligible": True}
    token = headers["Authorization"].removeprefix("Bearer ")
    customer_id = db.get(AuthSession, digest(token)).customer_id
    second_token = new_session(db, customer_id=customer_id)["token"]
    db.commit()
    second_headers = {"Authorization": "Bearer " + second_token}
    assert client.post(PATH, headers=second_headers).json() == {"eligible": False}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get(PATH, headers=second_headers).json() == {"eligible": False}
    address = client.post(
        "/api/v1/addresses",
        headers=second_headers,
        json={
            "recipient_name": "Sam",
            "phone": "9876543210",
            "line1": "Market road",
            "city": "Town",
            "state": "Karnataka",
        },
    )
    assert address.status_code == 201
    assert (
        client.delete(
            f"/api/v1/addresses/{address.json()['id']}", headers=second_headers
        ).status_code
        == 204
    )
    assert client.get(PATH, headers=second_headers).json() == {"eligible": False}


def test_existing_address_suppresses_offer_without_consuming_it(client, data):
    headers = data["headers"]
    assert client.get(PATH, headers=headers).json() == {"eligible": False}
    assert client.post(PATH, headers=headers).json() == {"eligible": False}
    client.delete(f"/api/v1/addresses/{data['address'].id}", headers=headers)
    assert client.get(PATH, headers=headers).json() == {"eligible": True}


def test_address_added_between_read_and_claim_prevents_offer(client, data):
    headers = data["headers"]
    client.delete(f"/api/v1/addresses/{data['address'].id}", headers=headers)
    assert client.get(PATH, headers=headers).json() == {"eligible": True}
    client.post(
        "/api/v1/addresses",
        headers=headers,
        json={
            "recipient_name": "Sam",
            "phone": "9876543210",
            "line1": "Market road",
            "city": "Town",
            "state": "Karnataka",
        },
    )
    assert client.post(PATH, headers=headers).json() == {"eligible": False}


def test_onboarding_requires_customer_session(client, data):
    for method in [client.get, client.post]:
        assert method(PATH).status_code == 401
        assert (
            method(PATH, headers={"Authorization": "Bearer " + data["admin_token"]}).status_code
            == 401
        )


def test_concurrent_devices_receive_only_one_offer(db):
    customer = Customer(google_subject="concurrent-address-onboarding")
    db.add(customer)
    db.commit()
    customer_id = customer.id
    barrier = Barrier(2)

    def claim():
        with Session(db.get_bind(), expire_on_commit=False) as session:
            # Both requests begin with an unconsumed Customer in their identity map.
            loaded = session.get(Customer, customer_id)
            assert not loaded.address_onboarding_seen
            barrier.wait(timeout=5)
            result = customer_data.address_onboarding(session, customer_id, claim=True)
            session.commit()
            return result["eligible"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))
    assert sorted(results) == [False, True]


def test_rolled_back_claim_does_not_consume_offer(db):
    customer = Customer(google_subject="rollback-address-onboarding")
    db.add(customer)
    db.commit()
    customer_id = customer.id
    assert customer_data.address_onboarding(db, customer_id, claim=True)["eligible"]
    db.rollback()
    assert customer_data.address_onboarding(db, customer_id)["eligible"]
