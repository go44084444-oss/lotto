from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings

ADMIN_HEADERS = {"X-Admin-Api-Key": settings.admin_api_key}


def test_create_draw_without_api_key_is_rejected(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [6, 7, 11, 15, 39, 43], "bonus_no": 20},
    )
    assert resp.status_code == 422  # Header(...) 필수값 누락


def test_create_draw_with_wrong_api_key_is_rejected(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [6, 7, 11, 15, 39, 43], "bonus_no": 20},
        headers={"X-Admin-Api-Key": "wrong-key"},
    )
    assert resp.status_code == 401


def test_create_draw_succeeds_and_is_retrievable(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1237, "numbers": [10, 20, 23, 34, 37, 40], "bonus_no": 36},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["draw_no"] == 1237
    assert body["numbers"] == [10, 20, 23, 34, 37, 40]
    assert body["bonus_no"] == 36
    assert body["draw_date"] == "2026-08-15"  # 1회(2002-12-07) + 7*1236일

    resp2 = client.get("/draws/1237")
    assert resp2.status_code == 200
    assert resp2.json()["numbers"] == [10, 20, 23, 34, 37, 40]


def test_create_draw_sorts_unordered_numbers(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [43, 6, 39, 11, 7, 15], "bonus_no": 20},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["numbers"] == [6, 7, 11, 15, 39, 43]


def test_create_draw_duplicate_draw_no_returns_409(
    client: TestClient, db_session: Session
) -> None:
    from datetime import date

    from app.models.draw import Draw

    db_session.add(
        Draw(
            draw_no=1237,
            n1=10,
            n2=20,
            n3=23,
            n4=34,
            n5=37,
            n6=40,
            bonus_no=36,
            draw_date=date(2026, 8, 15),
            source="manual",
        )
    )
    db_session.commit()

    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1237, "numbers": [1, 2, 3, 4, 5, 6], "bonus_no": 7},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409


def test_create_draw_rejects_duplicate_numbers(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [6, 6, 11, 15, 39, 43], "bonus_no": 20},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 422


def test_create_draw_rejects_bonus_overlapping_numbers(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [6, 7, 11, 15, 39, 43], "bonus_no": 6},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 422


def test_create_draw_rejects_out_of_range_numbers(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1235, "numbers": [0, 7, 11, 15, 39, 43], "bonus_no": 20},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 422


def test_create_draw_accepts_explicit_draw_date_override(client: TestClient) -> None:
    resp = client.post(
        "/admin/draws",
        json={
            "draw_no": 1235,
            "numbers": [6, 7, 11, 15, 39, 43],
            "bonus_no": 20,
            "draw_date": "2026-08-01",
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["draw_date"] == "2026-08-01"
