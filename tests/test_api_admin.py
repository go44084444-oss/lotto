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


def test_create_draw_auto_links_the_cycle_active_that_week(
    client: TestClient, db_session: Session
) -> None:
    """1238회(2026-08-22, 토) 등록 시, 그 주 리셋 직전까지 활성이었던 주차에
    자동으로 연결돼야 win-check가 바로 동작한다."""
    from datetime import datetime, timezone

    from app.models.assignment import WeeklyCycle

    cycle = WeeklyCycle(
        cycle_key=datetime(2026, 8, 15, tzinfo=timezone.utc).date(),
        starts_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(cycle)
    db_session.commit()
    db_session.refresh(cycle)

    resp = client.post(
        "/admin/draws",
        json={"draw_no": 1238, "numbers": [2, 13, 18, 32, 38, 42], "bonus_no": 22},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201

    db_session.refresh(cycle)
    assert cycle.associated_draw_no == 1238


def test_list_weekly_cycles_requires_admin(client: TestClient) -> None:
    resp = client.get("/admin/weekly-cycles")
    assert resp.status_code == 422

    resp2 = client.get("/admin/weekly-cycles", headers={"X-Admin-Api-Key": "wrong"})
    assert resp2.status_code == 401


def test_link_draw_to_cycle_success_and_errors(
    client: TestClient, db_session: Session
) -> None:
    from datetime import datetime, timezone

    from app.models.assignment import WeeklyCycle
    from app.models.draw import Draw

    cycle = WeeklyCycle(
        cycle_key=datetime(2026, 8, 15, tzinfo=timezone.utc).date(),
        starts_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(cycle)
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
            draw_date=datetime(2026, 8, 15).date(),
            source="manual",
        )
    )
    db_session.commit()
    db_session.refresh(cycle)

    resp_missing_draw = client.post(
        f"/admin/weekly-cycles/{cycle.id}/link-draw",
        json={"draw_no": 9999},
        headers=ADMIN_HEADERS,
    )
    assert resp_missing_draw.status_code == 404

    resp_missing_cycle = client.post(
        "/admin/weekly-cycles/999999/link-draw",
        json={"draw_no": 1237},
        headers=ADMIN_HEADERS,
    )
    assert resp_missing_cycle.status_code == 404

    resp_ok = client.post(
        f"/admin/weekly-cycles/{cycle.id}/link-draw",
        json={"draw_no": 1237},
        headers=ADMIN_HEADERS,
    )
    assert resp_ok.status_code == 200
    assert resp_ok.json()["associated_draw_no"] == 1237


def test_notify_winners_requires_linked_draw(
    client: TestClient, db_session: Session
) -> None:
    from datetime import datetime, timezone

    from app.models.assignment import WeeklyCycle

    cycle = WeeklyCycle(
        cycle_key=datetime(2026, 8, 15, tzinfo=timezone.utc).date(),
        starts_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(cycle)
    db_session.commit()
    db_session.refresh(cycle)

    resp = client.post(
        f"/admin/weekly-cycles/{cycle.id}/notify-winners", headers=ADMIN_HEADERS
    )
    assert resp.status_code == 409

    resp_missing_cycle = client.post(
        "/admin/weekly-cycles/999999/notify-winners", headers=ADMIN_HEADERS
    )
    assert resp_missing_cycle.status_code == 404


def test_notify_winners_counts_matching_members(
    client: TestClient, db_session: Session
) -> None:
    from datetime import datetime, timezone

    from app.models.assignment import Assignment, WeeklyCycle
    from app.models.combination import CombinationPool
    from app.models.draw import Draw

    winning_numbers = [2, 13, 18, 32, 38, 42]
    db_session.add(
        Draw(
            draw_no=1238,
            n1=2,
            n2=13,
            n3=18,
            n4=32,
            n5=38,
            n6=42,
            bonus_no=22,
            draw_date=datetime(2026, 8, 22).date(),
            source="manual",
        )
    )
    db_session.commit()

    cycle = WeeklyCycle(
        cycle_key=datetime(2026, 8, 15, tzinfo=timezone.utc).date(),
        starts_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
        associated_draw_no=1238,
    )
    db_session.add(cycle)
    db_session.add(CombinationPool(id=1, numbers=winning_numbers, combo_key=1))
    db_session.add(CombinationPool(id=2, numbers=[1, 3, 4, 5, 6, 7], combo_key=2))
    db_session.commit()
    db_session.refresh(cycle)

    reg = client.post(
        "/auth/register", json={"email": "winner@example.com", "password": "hunter2"}
    )
    member_id = client.get(
        "/me", headers={"Authorization": f"Bearer {reg.json()['access_token']}"}
    ).json()["id"]

    db_session.add(
        Assignment(weekly_cycle_id=cycle.id, member_id=member_id, combination_id=1)
    )
    db_session.add(
        Assignment(weekly_cycle_id=cycle.id, member_id=member_id, combination_id=2)
    )
    db_session.commit()

    resp = client.post(
        f"/admin/weekly-cycles/{cycle.id}/notify-winners", headers=ADMIN_HEADERS
    )
    assert resp.status_code == 200
    assert resp.json() == {"notified_members": 1, "winning_combinations": 1}


def test_regenerate_pool_requires_admin(client: TestClient) -> None:
    resp = client.post("/admin/combination-pool/regenerate", json={})
    assert resp.status_code == 422

    resp2 = client.post(
        "/admin/combination-pool/regenerate",
        json={},
        headers={"X-Admin-Api-Key": "wrong"},
    )
    assert resp2.status_code == 401


def test_regenerate_pool_rejects_when_assignments_exist_and_not_reset(
    client: TestClient, db_session: Session
) -> None:
    from datetime import datetime, timezone

    from app.models.assignment import Assignment, WeeklyCycle
    from app.models.combination import CombinationPool

    cycle = WeeklyCycle(
        cycle_key=datetime(2026, 8, 15, tzinfo=timezone.utc).date(),
        starts_at=datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc),
    )
    db_session.add(cycle)
    db_session.add(CombinationPool(id=1, numbers=[1, 2, 3, 4, 5, 6], combo_key=1))
    db_session.commit()
    db_session.refresh(cycle)

    reg = client.post(
        "/auth/register", json={"email": "poolreset@example.com", "password": "hunter2"}
    )
    member_id = client.get(
        "/me", headers={"Authorization": f"Bearer {reg.json()['access_token']}"}
    ).json()["id"]
    db_session.add(
        Assignment(weekly_cycle_id=cycle.id, member_id=member_id, combination_id=1)
    )
    db_session.commit()

    resp = client.post(
        "/admin/combination-pool/regenerate",
        json={"reset_assignments": False},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 409
