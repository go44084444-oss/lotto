"""회원 주간 배분 로직 — 같은 주 내 중복 배정 금지의 실제 정합성 근원은
`assignments.uq_assignment_no_overlap`(DB UNIQUE 제약)이다. 여기서는 그 제약 위반을
최소화하기 위해 `FOR UPDATE SKIP LOCKED`로 동시 요청 간 후보 조합을 분산시킨다.

절대 draws 테이블을 참조하지 않는다 — 과거 당첨 조합을 판매 풀에서 제외하는 로직은
이미 검토 후 기각되었다.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.member import Member, MembershipTier
from app.services.week_service import get_or_create_current_cycle

MAX_ATTEMPTS = 5

_CANDIDATE_QUERY = text(
    """
    SELECT cp.id
    FROM combination_pool cp
    WHERE NOT EXISTS (
        SELECT 1 FROM assignments a
        WHERE a.weekly_cycle_id = :cycle_id AND a.combination_id = cp.id
    )
    ORDER BY random()
    LIMIT :n
    FOR UPDATE SKIP LOCKED
    """
)


class MemberWithdrawnError(Exception):
    pass


class InsufficientPoolError(Exception):
    pass


def _current_assignments(db: Session, cycle_id: int, member_id: int) -> list[Assignment]:
    return (
        db.query(Assignment)
        .filter(Assignment.weekly_cycle_id == cycle_id, Assignment.member_id == member_id)
        .all()
    )


def assign_for_member(db: Session, member: Member) -> list[Assignment]:
    """멱등: 이번 주 이미 배정이 있으면 그대로 반환한다."""
    if member.status != "active":
        raise MemberWithdrawnError(f"member {member.id}는 탈퇴 상태입니다.")

    cycle = get_or_create_current_cycle(db)

    existing = _current_assignments(db, cycle.id, member.id)
    if existing:
        return existing

    tier = db.get(MembershipTier, member.tier)
    quota = tier.weekly_quota

    assigned: list[Assignment] = []
    remaining = quota
    for _ in range(MAX_ATTEMPTS):
        if remaining <= 0:
            break

        candidate_ids = (
            db.execute(_CANDIDATE_QUERY, {"cycle_id": cycle.id, "n": remaining}).scalars().all()
        )
        if not candidate_ids:
            break

        for combo_id in candidate_ids:
            db.add(
                Assignment(
                    weekly_cycle_id=cycle.id, member_id=member.id, combination_id=combo_id
                )
            )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue  # 동시 요청과 충돌 — 부족분만 다시 시도

        assigned = _current_assignments(db, cycle.id, member.id)
        remaining = quota - len(assigned)

    if len(assigned) < quota:
        raise InsufficientPoolError(
            f"member {member.id}: {len(assigned)}/{quota}개만 배정됨 — "
            "풀 소진 또는 과도한 동시성 충돌로 추정됩니다."
        )

    return assigned
