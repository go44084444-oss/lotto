from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.models.assignment import WeeklyCycle
from app.models.combination import CombinationPool
from app.models.member import Member, MembershipTier
from app.services import assignment_service

CYCLE_START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _seed_pool(db: Session, size: int) -> None:
    for i in range(size):
        db.merge(
            CombinationPool(id=i + 1, numbers=[1, 2, 3, 4, 5, (i % 40) + 6], combo_key=i + 1)
        )


def test_idempotent_repeat_request_returns_same_assignments(db_session: Session) -> None:
    db_session.merge(MembershipTier(code="free", weekly_quota=5, display_name="무료 회원"))
    _seed_pool(db_session, 50)
    member = Member(email="idem@test.local", tier="free", hashed_password="x")
    db_session.add(member)
    db_session.add(WeeklyCycle(cycle_key=CYCLE_START.date(), starts_at=CYCLE_START))
    db_session.commit()
    db_session.refresh(member)

    first = assignment_service.assign_for_member(db_session, member)
    second = assignment_service.assign_for_member(db_session, member)

    assert {a.combination_id for a in first} == {a.combination_id for a in second}
    assert len(first) == 5


def test_withdrawn_member_is_rejected(db_session: Session) -> None:
    db_session.merge(MembershipTier(code="free", weekly_quota=5, display_name="무료 회원"))
    _seed_pool(db_session, 50)
    member = Member(email="withdrawn@test.local", tier="free", status="withdrawn", hashed_password="x")
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)

    with pytest.raises(assignment_service.MemberWithdrawnError):
        assignment_service.assign_for_member(db_session, member)


def test_quota_follows_membership_tier(db_session: Session) -> None:
    db_session.merge(MembershipTier(code="free", weekly_quota=3, display_name="무료 회원"))
    _seed_pool(db_session, 50)
    member = Member(email="quota@test.local", tier="free", hashed_password="x")
    db_session.add(member)
    db_session.add(WeeklyCycle(cycle_key=CYCLE_START.date(), starts_at=CYCLE_START))
    db_session.commit()
    db_session.refresh(member)

    assigned = assignment_service.assign_for_member(db_session, member)
    assert len(assigned) == 3
