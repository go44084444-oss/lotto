from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription


def _register(client, email: str, password: str = "hunter2") -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_vapid_public_key_is_public(client) -> None:
    resp = client.get("/push/vapid-public-key")
    assert resp.status_code == 200
    assert "vapid_public_key" in resp.json()


def test_create_push_subscription_without_auth_returns_401(client) -> None:
    resp = client.post(
        "/me/push-subscriptions",
        json={"endpoint": "https://push.example/abc", "keys": {"p256dh": "p", "auth": "a"}},
    )
    assert resp.status_code == 401


def test_create_then_delete_push_subscription(client, db_session: Session) -> None:
    headers = _register(client, "push@example.com")

    resp = client.post(
        "/me/push-subscriptions",
        json={"endpoint": "https://push.example/abc", "keys": {"p256dh": "p", "auth": "a"}},
        headers=headers,
    )
    assert resp.status_code == 204
    assert db_session.query(PushSubscription).count() == 1

    resp2 = client.request(
        "DELETE",
        "/me/push-subscriptions",
        params={"endpoint": "https://push.example/abc"},
        headers=headers,
    )
    assert resp2.status_code == 204
    assert db_session.query(PushSubscription).count() == 0


def test_create_push_subscription_upserts_on_same_endpoint(
    client, db_session: Session
) -> None:
    headers_a = _register(client, "push-a@example.com")
    headers_b = _register(client, "push-b@example.com")

    client.post(
        "/me/push-subscriptions",
        json={"endpoint": "https://push.example/shared", "keys": {"p256dh": "p1", "auth": "a1"}},
        headers=headers_a,
    )
    resp = client.post(
        "/me/push-subscriptions",
        json={"endpoint": "https://push.example/shared", "keys": {"p256dh": "p2", "auth": "a2"}},
        headers=headers_b,
    )

    assert resp.status_code == 204
    assert db_session.query(PushSubscription).count() == 1
    sub = db_session.query(PushSubscription).one()
    assert sub.p256dh == "p2"
