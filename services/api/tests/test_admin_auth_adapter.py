def owner(client, data):
    client.cookies.set("gg_admin", data["admin_token"])
    return {"Origin": "http://localhost:3000"}


def test_mobile_and_browser_admin_sessions_use_separate_transports(client, data):
    login = client.post(
        "/api/v1/admin/auth/mobile-login",
        json={"username": "owner", "password": "a-secure-test-password"},
    )
    assert login.status_code == 200, login.text
    assert "gg_admin" not in login.headers.get("set-cookie", "")

    bearer = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/api/v1/admin/me", headers=bearer).status_code == 200
    assert client.get("/api/v1/orders", headers=bearer).status_code == 401
    assert client.post("/api/v1/admin/auth/logout", headers=bearer).status_code == 204
    assert client.get("/api/v1/admin/me", headers=bearer).status_code == 401

    cookie_headers = owner(client, data)
    assert client.get("/api/v1/admin/me", headers=cookie_headers).status_code == 200
    assert (
        client.post("/api/v1/admin/brands", json={"name": "Blocked", "slug": "blocked"}).status_code
        == 403
    )


def test_admin_browser_login_maps_credentials_and_sets_http_only_cookie(client, data):
    headers = {"Origin": "http://localhost:3000"}
    assert (
        client.post(
            "/api/v1/admin/auth/login",
            json={"username": "owner", "password": "wrong"},
            headers=headers,
        ).status_code
        == 401
    )

    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "owner", "password": "a-secure-test-password"},
        headers=headers,
    )

    assert response.status_code == 200
    assert "httponly" in response.headers["set-cookie"].lower()


def test_admin_mobile_login_rejects_browser_origin(client):
    response = client.post(
        "/api/v1/admin/auth/mobile-login",
        json={"username": "owner", "password": "a-secure-test-password"},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
