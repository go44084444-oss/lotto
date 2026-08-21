from sqlalchemy.orm import Session

from app.models.combination import CombinationPool


def _seed_pool(db_session: Session, size: int) -> None:
    for i in range(size):
        db_session.merge(
            CombinationPool(id=i + 1, numbers=[1, 2, 3, 4, 5, (i % 40) + 6], combo_key=i + 1)
        )
    db_session.commit()


def _register(client, email: str, password: str = "hunter2") -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_request_assignment_returns_201_then_view_current(client, db_session: Session) -> None:
    _seed_pool(db_session, 50)
    headers = _register(client, "assign@example.com")

    resp = client.post("/me/assignments", headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["quota"] == 20
    assert len(body["combinations"]) == 20

    current = client.get("/me/assignments/current", headers=headers)
    assert current.status_code == 200
    assert {c["id"] for c in current.json()["combinations"]} == {
        c["id"] for c in body["combinations"]
    }


def test_request_assignment_is_idempotent_and_returns_200_on_repeat(
    client, db_session: Session
) -> None:
    _seed_pool(db_session, 50)
    headers = _register(client, "idem-api@example.com")

    first = client.post("/me/assignments", headers=headers)
    second = client.post("/me/assignments", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 200
    assert {c["id"] for c in first.json()["combinations"]} == {
        c["id"] for c in second.json()["combinations"]
    }


def test_assignment_without_token_returns_401(client) -> None:
    resp = client.post("/me/assignments")
    assert resp.status_code == 401


def test_current_assignment_before_any_request_is_empty(client, db_session: Session) -> None:
    _seed_pool(db_session, 50)
    headers = _register(client, "noassign@example.com")

    resp = client.get("/me/assignments/current", headers=headers)

    assert resp.status_code == 200
    assert resp.json()["combinations"] == []


def test_win_check_without_draw_result_returns_404(client, db_session: Session) -> None:
    _seed_pool(db_session, 50)
    headers = _register(client, "wc@example.com")
    client.post("/me/assignments", headers=headers)

    resp = client.get("/me/assignments/win-check", headers=headers)

    assert resp.status_code == 404


def test_another_members_token_cannot_see_my_assignment(
    client, db_session: Session
) -> None:
    """소유권 검증: 다른 회원의 토큰으로는 내 배정이 보이지 않아야 한다(둘 다 자기 것만 봄)."""
    _seed_pool(db_session, 50)
    headers_a = _register(client, "member-a@example.com")
    headers_b = _register(client, "member-b@example.com")

    resp_a = client.post("/me/assignments", headers=headers_a).json()
    resp_b = client.post("/me/assignments", headers=headers_b).json()

    ids_a = {c["id"] for c in resp_a["combinations"]}
    ids_b = {c["id"] for c in resp_b["combinations"]}
    assert ids_a.isdisjoint(ids_b)
