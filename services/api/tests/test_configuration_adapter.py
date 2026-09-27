def test_config_maps_first_release_checkout_capabilities(client):
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    assert response.json()["online_upi_enabled"] is False
