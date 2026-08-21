"""'현재 주'를 weekly_cycles 테이블 기반으로 해석한다. 스케줄러가 지연/장애 상태여도
요청이 들어오면 이 함수가 활성 주기를 만들어내므로 시스템이 견고하게 동작한다."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

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
