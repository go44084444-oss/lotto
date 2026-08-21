def _register(client, email: str, password: str = "hunter2") -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_me_returns_current_member(client) -> None:
    headers = _register(client, "me@example.com")
    resp = client.get("/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "me@example.com"
    assert body["status"] == "active"
    assert body["tier"] == "free"


def test_get_me_without_token_returns_401(client) -> None:
    resp = client.get("/me")
    assert resp.status_code == 401


def test_get_me_with_invalid_token_returns_401(client) -> None:
    resp = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_withdraw_me_sets_status(client) -> None:
    headers = _register(client, "wd@example.com")
    resp = client.post("/me/withdraw", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"


def test_me_cannot_see_another_members_data(client) -> None:
    """소유권 검증: 서로 다른 토큰은 서로 다른 회원만 조회할 수 있어야 한다."""
    headers_a = _register(client, "owner-a@example.com")
    headers_b = _register(client, "owner-b@example.com")

    resp_a = client.get("/me", headers=headers_a).json()
    resp_b = client.get("/me", headers=headers_b).json()

    assert resp_a["email"] != resp_b["email"]
    assert resp_a["id"] != resp_b["id"]
