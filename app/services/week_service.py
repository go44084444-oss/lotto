"""'현재 주'를 weekly_cycles 테이블 기반으로 해석한다. 스케줄러가 지연/장애 상태여도
요청이 들어오면 이 함수가 활성 주기를 만들어내므로 시스템이 견고하게 동작한다."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.assignment import WeeklyCycle


def get_or_create_current_cycle(db: Session) -> WeeklyCycle:
    now = datetime.now(timezone.utc)
    cycle = (
        db.query(WeeklyCycle)
        .filter(
            WeeklyCycle.starts_at <= now,
            or_(WeeklyCycle.ends_at.is_(None), WeeklyCycle.ends_at > now),
        )
        .order_by(WeeklyCycle.starts_at.desc())
        .first()
    )
    if cycle is not None:
        return cycle

    cycle = WeeklyCycle(cycle_key=now.date(), starts_at=now)
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def rollover(db: Session) -> WeeklyCycle:
    """수동/스케줄러 트리거 공용 롤오버. 정확한 컷오버 시각은 아직 미확정
    (TODO(product): config.py의 WEEK_RESET_* 참고)."""
    now = datetime.now(timezone.utc)
    current = get_or_create_current_cycle(db)
    current.ends_at = now

    new_cycle = WeeklyCycle(cycle_key=now.date(), starts_at=now)
    db.add(new_cycle)
    db.commit()
    db.refresh(new_cycle)
    return new_cycle


def find_cycle_for_draw_date(db: Session, draw_date: date) -> WeeklyCycle | None:
    """당첨번호가 등록될 때, 그 회차가 속한 주(리셋 직전까지 활성이었던 주차)를 찾는다.
    리셋 시각(WEEK_RESET_*) 1분 전 시점을 기준으로 활성 주차를 조회해, 추첨 당일 리셋이
    이미 일어난 뒤에 당첨번호가 입력되더라도 올바른(추첨 전) 주차에 연결되게 한다."""
    tz = ZoneInfo(settings.week_reset_timezone)
    hour, minute = (int(x) for x in settings.week_reset_time.split(":"))
    reset_at_local = datetime.combine(draw_date, time(hour, minute), tzinfo=tz)
    just_before_reset = reset_at_local.astimezone(timezone.utc) - timedelta(minutes=1)

    return (
        db.query(WeeklyCycle)
        .filter(
            WeeklyCycle.starts_at <= just_before_reset,
            or_(WeeklyCycle.ends_at.is_(None), WeeklyCycle.ends_at > just_before_reset),
        )
        .order_by(WeeklyCycle.starts_at.desc())
        .first()
    )
