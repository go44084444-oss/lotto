"""회원 주간 배분 로직 — 같은 주 내 중복 배정 금지의 실제 정합성 근원은
`assignments.uq_assignment_no_overlap`(DB UNIQUE 제약)이다. 여기서는 그 제약 위반을
최소화하기 위해 `FOR UPDATE SKIP LOCKED`로 동시 요청 간 후보 조합을 분산시킨다.

절대 draws 테이블을 참조하지 않는다 — 과거 당첨 조합을 판매 풀에서 제외하는 로직은
이미 검토 후 기각되었다.
"""

from __future__ import annotations

import random
from collections import Counter

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.member import Member, MembershipTier
from app.services.week_service import get_or_create_current_cycle

MAX_ATTEMPTS = 5

NUMBER_REPEAT_SOFT_CAP = 3
"""한 회원의 배치 하나(예: 20개) 안에서 같은 숫자가 이 횟수를 넘지 않도록 하는
선호치 — 하드 제한이 아니다. 만족하는 후보가 부족해도 있는 만큼은 그대로
쓰므로 멱등성/소진 계약(quota 달성 또는 InsufficientPoolError)에는 영향이 없다.
당첨 확률도 바꾸지 않는다 — 어떤 조합이든 확률은 동일하며, 이 로직은 한 회원에게
나가는 배치의 '구성'만 조정해 같은 숫자가 눈에 띄게 반복되는 것을 줄인다."""

CHUNK_SIZE = 4
"""한 라운드에서 한꺼번에 요청하는 최대 개수. 숫자 반복 회피는 '지금까지 이 배치
에서 고른 숫자'를 기준으로 하므로, 한 라운드에 quota 전체(예: 20개)를 한 번에
받아오면 그 20개 전부가 같은(텅 빈) 기준으로 뽑혀 선호가 사실상 적용되지 않는다
— CHUNK_SIZE 단위로 나눠야 라운드 사이에 숫자 구성이 갱신되어 실제로 효과가
있다."""

SAMPLE_OVERSAMPLE_FACTOR = 4
SAMPLE_ROUNDS = 5
"""`ORDER BY random()`는 combination_pool 테이블(357만 행) 전체를 정렬해야 해서
호출당 ~1초가 걸린다 — 여러 번 부르면 그만큼 느려진다(다양성 로직을 처음 넣었을 때
겪은 문제). 대신 id가 1..MAX(id) 사이에 빈틈없이 연속이라는 성질을 이용해, 그
범위에서 무작위 정수를 몇 개 뽑아 `id = ANY(...)`로 조회한다 — 기본키 인덱스를
타므로 테이블 크기와 무관하게 항상 빠르다(실측 ~2ms). 뽑은 무작위 id 중 이미
배정됐거나 제외 대상인 것이 섞여 있을 수 있어 필요한 개수보다 넉넉히
(SAMPLE_OVERSAMPLE_FACTOR배) 뽑고, 그래도 부족하면 같은 청크에서 최대
SAMPLE_ROUNDS번까지 새로 무작위 id를 뽑아 재시도한다. 풀이 거의 소진돼 무작위
표본이 계속 빗나가는(현실에서는 사실상 없는) 극단적인 경우에 대비해, 그래도
부족하면 아래 _FALLBACK_QUERY로 테이블 전체를 훑어 확실히 채운다."""

_CANDIDATE_QUERY = text(
    """
    SELECT cp.id, cp.numbers
    FROM combination_pool cp
    WHERE cp.id = ANY(CAST(:ids AS integer[]))
    AND NOT EXISTS (
        SELECT 1 FROM assignments a
        WHERE a.weekly_cycle_id = :cycle_id AND a.combination_id = cp.id
    )
    AND NOT (cp.id = ANY(CAST(:exclude_ids AS integer[])))
    ORDER BY (cp.numbers && CAST(:avoid_numbers AS smallint[])), random()
    LIMIT :n
    FOR UPDATE SKIP LOCKED
    """
)

_FALLBACK_QUERY = text(
    """
    SELECT cp.id, cp.numbers
    FROM combination_pool cp
    WHERE NOT EXISTS (
        SELECT 1 FROM assignments a
        WHERE a.weekly_cycle_id = :cycle_id AND a.combination_id = cp.id
    )
    AND NOT (cp.id = ANY(CAST(:exclude_ids AS integer[])))
    ORDER BY random()
    LIMIT :n
    FOR UPDATE SKIP LOCKED
    """
)


def _max_pool_id(db: Session) -> int:
    return db.execute(text("SELECT MAX(id) FROM combination_pool")).scalar_one()


def _pick_chunk(
    db: Session, cycle_id: int, n: int, exclude_ids: list[int], avoid_numbers: list[int]
) -> list[tuple[int, list[int]]]:
    """id 범위에서 무작위 정수를 뽑아 기본키로 바로 조회하는 방식으로 최대 n개를
    빠르게 고른다(위 SAMPLE_* 설명 참고). 정확히 필요한 만큼만 원자적으로
    잠근다(FOR UPDATE SKIP LOCKED)."""
    max_id = _max_pool_id(db)
    if max_id is None:
        return []

    picked: list[tuple[int, list[int]]] = []
    for _ in range(SAMPLE_ROUNDS):
        need = n - len(picked)
        if need <= 0:
            break

        sample_size = min(max_id, need * SAMPLE_OVERSAMPLE_FACTOR + 10)
        ids = random.sample(range(1, max_id + 1), sample_size)
        rows = db.execute(
            _CANDIDATE_QUERY,
            {
                "cycle_id": cycle_id,
                "ids": ids,
                "n": need,
                "exclude_ids": exclude_ids + [combo_id for combo_id, _ in picked],
                "avoid_numbers": avoid_numbers,
            },
        ).all()
        picked.extend((row.id, row.numbers) for row in rows)

    need = n - len(picked)
    if need > 0:
        rows = db.execute(
            _FALLBACK_QUERY,
            {
                "cycle_id": cycle_id,
                "n": need,
                "exclude_ids": exclude_ids + [combo_id for combo_id, _ in picked],
            },
        ).all()
        picked.extend((row.id, row.numbers) for row in rows)

    return picked


def _pick_candidates(db: Session, cycle_id: int, n: int) -> list[int]:
    """n개를 CHUNK_SIZE 단위로 나눠 고른다 — 청크마다 지금까지 이 배치에서
    NUMBER_REPEAT_SOFT_CAP에 도달한 숫자를 ORDER BY로 뒤로 미뤄 선호도 수준에서
    피한다(청크로 나누지 않으면 avoid_numbers가 갱신될 기회가 없어 선호가
    사실상 적용되지 않는다)."""
    selected: list[int] = []
    number_counts: Counter[int] = Counter()

    while len(selected) < n:
        chunk_n = min(CHUNK_SIZE, n - len(selected))
        avoid_numbers = [
            num for num, count in number_counts.items() if count >= NUMBER_REPEAT_SOFT_CAP
        ]
        picked = _pick_chunk(db, cycle_id, chunk_n, selected, avoid_numbers)
        if not picked:
            break

        for combo_id, numbers in picked:
            selected.append(combo_id)
            number_counts.update(numbers)

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
