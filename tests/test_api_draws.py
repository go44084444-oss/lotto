from datetime import date

from sqlalchemy.orm import Session

from app.models.draw import Draw


def _seed_draw(
    db_session: Session,
    draw_no: int,
    numbers: list[int],
    bonus_no: int,
    draw_date: date,
) -> None:
    db_session.add(
        Draw(
            draw_no=draw_no,
            n1=numbers[0],
            n2=numbers[1],
            n3=numbers[2],
            n4=numbers[3],
            n5=numbers[4],
            n6=numbers[5],
            bonus_no=bonus_no,
            draw_date=draw_date,
            source="test",
        )
    )
    db_session.commit()


def test_get_known_draw(client, db_session: Session) -> None:
    _seed_draw(db_session, 1237, [10, 20, 23, 34, 37, 40], 36, date(2026, 8, 15))

    resp = client.get("/draws/1237")

    assert resp.status_code == 200
    body = resp.json()
    assert body["numbers"] == [10, 20, 23, 34, 37, 40]
    assert body["bonus_no"] == 36


def test_get_unknown_draw_returns_404(client) -> None:
    resp = client.get("/draws/999999")
    assert resp.status_code == 404


def test_latest_draw_returns_highest_draw_no(client, db_session: Session) -> None:
    _seed_draw(db_session, 1, [1, 2, 3, 4, 5, 6], 7, date(2002, 12, 7))
    _seed_draw(db_session, 2, [2, 3, 4, 5, 6, 7], 8, date(2002, 12, 14))

    resp = client.get("/draws/latest")

    assert resp.status_code == 200
    assert resp.json()["draw_no"] == 2


def test_list_draws_ordered_desc(client, db_session: Session) -> None:
    _seed_draw(db_session, 1, [1, 2, 3, 4, 5, 6], 7, date(2002, 12, 7))
    _seed_draw(db_session, 2, [2, 3, 4, 5, 6, 7], 8, date(2002, 12, 14))

    resp = client.get("/draws")

    assert resp.status_code == 200
    assert [d["draw_no"] for d in resp.json()] == [2, 1]
