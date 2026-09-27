from datetime import timedelta

from app.models.domain import AuthSession, now
from app.services.auth import digest


def test_session_dependencies_reject_expiry_and_wrong_identity_type(client, db, data):
    token = data["headers"]["Authorization"].removeprefix("Bearer ")
    row = db.get(AuthSession, digest(token))
    row.expires_at = now() - timedelta(seconds=1)
    db.commit()

    assert client.get("/api/v1/orders", headers=data["headers"]).status_code == 401
    assert (
        client.get(
            "/api/v1/orders",
            headers={"Authorization": "Bearer " + data["admin_token"]},
        ).status_code
        == 401
    )

    client.cookies.set("gg_admin", data["other_headers"]["Authorization"].removeprefix("Bearer "))
    assert client.get("/api/v1/admin/me").status_code == 401


def test_customer_logout_maps_to_no_content(client, data):
    response = client.post("/api/v1/auth/logout", headers=data["headers"])
    assert response.status_code == 204
    assert client.get("/api/v1/orders", headers=data["headers"]).status_code == 401
