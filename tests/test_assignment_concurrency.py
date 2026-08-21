from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.models.assignment import Assignment, WeeklyCycle
from app.models.combination import CombinationPool
from app.models.member import Member, MembershipTier
from app.services import assignment_service

CYCLE_START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _seed(engine: Engine, pool_size: int, member_count: int, quota: int) -> tuple[list[int], int]:
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as db:
        db.merge(MembershipTier(code="free", weekly_quota=quota, display_name="무료 회원"))

        for i in range(pool_size):
            db.merge(
                CombinationPool(id=i + 1, numbers=[1, 2, 3, 4, 5, (i % 40) + 6], combo_key=i + 1)
            )

        members = [
            Member(email=f"concurrency-{i}@test.local", tier="free", hashed_password="x")
            for i in range(member_count)
        ]
        db.add_all(members)

        cycle = WeeklyCycle(cycle_key=CYCLE_START.date(), starts_at=CYCLE_START)
        db.add(cycle)

        db.commit()
        for m in members:
            db.refresh(m)
        db.refresh(cycle)
        return [m.id for m in members], cycle.id


def _request_assignment(engine: Engine, member_id: int) -> list[int]:
    session_factory = sessionmaker(bind=engine, future=True)
    with session_factory() as db:
        member = db.get(Member, member_id)
        assignments = assignment_service.assign_for_member(db, member)
        return [a.combination_id for a in assignments]


def test_concurrent_requests_never_double_assign_within_week(test_engine: Engine) -> None:
    """검증②: 여러 회원이 동시에 배정을 요청해도 같은 주 내 조합 중복이 없어야 한다."""
    pool_size = 400
    member_count = 20
    quota = 20  # 20명 x 20개 = 400개 = 풀 크기(정확히 소진)

    member_ids, cycle_id = _seed(test_engine, pool_size, member_count, quota)

    with ThreadPoolExecutor(max_workers=member_count) as executor:
        futures = [executor.submit(_request_assignment, test_engine, mid) for mid in member_ids]
        results = [f.result() for f in as_completed(futures)]

    assert all(len(r) == quota for r in results)

    session_factory = sessionmaker(bind=test_engine, future=True)
    with session_factory() as db:
        duplicates = db.execute(
            select(Assignment.combination_id, func.count())
            .where(Assignment.weekly_cycle_id == cycle_id)
            .group_by(Assignment.combination_id)
            .having(func.count() > 1)
        ).all()
        assert duplicates == []

        total = db.execute(
            select(func.count()).where(Assignment.weekly_cycle_id == cycle_id)
        ).scalar_one()
        assert total == pool_size


def test_undersized_pool_raises_clear_error(test_engine: Engine) -> None:
    """풀이 부족하면 조용히 일부만 배정하지 않고 명확한 예외를 던져야 한다."""
    member_ids, _ = _seed(test_engine, pool_size=5, member_count=1, quota=20)

    session_factory = sessionmaker(bind=test_engine, future=True)
    with session_factory() as db:
        member = db.get(Member, member_ids[0])
        with pytest.raises(assignment_service.InsufficientPoolError):
            assignment_service.assign_for_member(db, member)
