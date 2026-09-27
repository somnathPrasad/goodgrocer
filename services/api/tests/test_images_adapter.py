def test_image_adapter_maps_invalid_content_to_customer_safe_error(client, data):
    client.cookies.set("gg_admin", data["admin_token"])
    response = client.post(
        "/api/v1/admin/images",
        files={"file": ("x.png", b"not an image", "image/png")},
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_IMAGE"
