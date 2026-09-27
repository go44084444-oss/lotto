"""회원 주간 배분 로직 — 같은 주 내 중복 배정 금지의 실제 정합성 근원은
`assignments.uq_assignment_no_overlap`(DB UNIQUE 제약)이다. 여기서는 그 제약 위반을
최소화하기 위해 `FOR UPDATE SKIP LOCKED`로 동시 요청 간 후보 조합을 분산시킨다.

절대 draws 테이블을 참조하지 않는다 — 과거 당첨 조합을 판매 풀에서 제외하는 로직은
이미 검토 후 기각되었다.
"""

from __future__ import annotations

from collections import Counter

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.member import Member, MembershipTier
from app.services.week_service import get_or_create_current_cycle

MAX_ATTEMPTS = 5

CHUNK_SIZE = 4
"""한 번에 잠글 후보 개수. quota=20이면 왕복 ~4회로, 숫자 하나당 매번 왕복하던
것보다 훨씬 빠르다. 각 청크는 원래 코드처럼 '요청한 만큼만 정확히' 한 번의 쿼리로
원자적으로 잠근다(FOR UPDATE SKIP LOCKED) — 쓰지 않을 행까지 잠가 다른 동시
요청을 불필요하게 막는 일이 없고, 후보가 없어 재시도용으로 한 번 더 왕복하는
일도 없다(아래 ORDER BY 선호 방식이라 항상 있는 만큼은 그대로 반환된다)."""

NUMBER_REPEAT_SOFT_CAP = 3
"""한 회원의 배치 하나(예: 20개) 안에서 같은 숫자가 이 횟수를 넘지 않도록 하는
선호치 — 하드 제한이 아니다. WHERE로 걸러내는 대신 ORDER BY로 '선호'만 하므로
후보가 0개로 떨어져 재시도가 필요해지는 일이 없다. 당첨 확률도 바꾸지 않는다 —
어떤 조합이든 확률은 동일하며, 이 로직은 한 회원에게 나가는 배치의 '구성'만
조정해 같은 숫자가 눈에 띄게 반복되는 것을 줄인다."""

_CANDIDATE_QUERY = text(
    """
    SELECT cp.id, cp.numbers
    FROM combination_pool cp
    WHERE NOT EXISTS (
        SELECT 1 FROM assignments a
        WHERE a.weekly_cycle_id = :cycle_id AND a.combination_id = cp.id
    )
    AND NOT (cp.id = ANY(CAST(:exclude_ids AS integer[])))
    ORDER BY (cp.numbers && CAST(:avoid_numbers AS smallint[])), random()
    LIMIT :n
    FOR UPDATE SKIP LOCKED
    """
)


def _pick_candidates(db: Session, cycle_id: int, n: int) -> list[int]:
    """n개를 CHUNK_SIZE 단위로 나눠, 매번 정확히 그만큼만 원자적으로 잠근다(원래
    코드와 동일한 '요청한 만큼만 정확히' 성질 유지). 청크마다 지금까지 이 배치에서
    NUMBER_REPEAT_SOFT_CAP에 도달한 숫자를 ORDER BY로 뒤로 미뤄 선호도 수준에서
    피한다 — WHERE 조건이 아니므로 만족하는 후보가 부족해도 있는 만큼은 그대로
    반환된다(별도 재시도 왕복이 필요 없다)."""
    selected: list[int] = []
    number_counts: Counter[int] = Counter()

    while len(selected) < n:
        chunk_n = min(CHUNK_SIZE, n - len(selected))
        avoid_numbers = [
            num for num, count in number_counts.items() if count >= NUMBER_REPEAT_SOFT_CAP
        ]
        rows = db.execute(
            _CANDIDATE_QUERY,
            {
                "cycle_id": cycle_id,
                "n": chunk_n,
                "exclude_ids": selected,
                "avoid_numbers": avoid_numbers,
            },
        ).all()

        if not rows:
            break

        for row in rows:
            selected.append(row.id)
            number_counts.update(row.numbers)

    return selected


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

        candidate_ids = _pick_candidates(db, cycle.id, remaining)
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
