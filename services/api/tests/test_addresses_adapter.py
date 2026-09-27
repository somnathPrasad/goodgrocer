def test_reverse_geocode_authenticates_and_validates_coordinates(client, data):
    path = "/api/v1/addresses/reverse-geocode?latitude=12.9&longitude=77.6"
    assert client.get(path).status_code == 401
    assert (
        client.get(
            "/api/v1/addresses/reverse-geocode?latitude=91&longitude=77.6",
            headers=data["headers"],
        ).status_code
        == 422
    )


def test_address_ownership_error_maps_to_not_found(client, data):
    body = {
        "recipient_name": "Sam",
        "phone": "9876543210",
        "line1": "12 Market Road",
        "city": "Town",
        "state": "Karnataka",
    }
    created = client.post("/api/v1/addresses", json=body, headers=data["headers"])

    assert created.status_code == 201
    assert created.json()["phone"] == "+919876543210"
    assert (
        client.put(
            f"/api/v1/addresses/{created.json()['id']}",
            json=body,
            headers=data["other_headers"],
        ).status_code
        == 404
    )
