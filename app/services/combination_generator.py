"""45개 중 6개를 뽑는 전체 조합(8,145,060개)을 순회하며 8개 필터를 적용하고,
생존 조합(~3,645,902개)을 combination_pool에 COPY로 대량 적재하는 1회성 배치 작업.

절대 draws 테이블을 참조하지 않는다 — 과거 당첨 조합을 판매 풀에서 제외하는 로직은
이미 검토 후 기각되었다.
"""

from __future__ import annotations

import itertools
import logging
from collections.abc import Iterator

from app.db.session import engine
from app.services.filters import Combo, passes_all_filters

logger = logging.getLogger(__name__)

UNIQUE_CONSTRAINT_NAME = "uq_combination_pool_combo_key"


def combo_key(nums: Combo) -> int:
    """45비트 비트마스크 인코딩 — 조합마다 고유하고 충돌 없는 BIGINT 값."""
    return sum(1 << (n - 1) for n in nums)


def generate_survivors() -> Iterator[Combo]:
    for combo in itertools.combinations(range(1, 46), 6):
        if passes_all_filters(combo):
            yield combo


def load_pool() -> int:
    """combination_pool을 비우고 필터 생존 조합으로 다시 채운다. 생존 조합 수를 반환."""
    raw_conn = engine.raw_connection()
    try:
        cur = raw_conn.cursor()
        cur.execute("SELECT count(*) FROM assignments")
        (assignment_count,) = cur.fetchone()
        if assignment_count > 0:
            raise RuntimeError(
                f"assignments 테이블에 {assignment_count}개의 배정 기록이 있어 "
                "combination_pool을 재생성할 수 없습니다. 기존 배정이 참조하는 조합 ID가 "
                "깨질 수 있으니, 재생성이 꼭 필요하면 배정 데이터를 먼저 검토/백업하세요."
            )
        # combination_pool을 참조하는 FK(assignments) 때문에 TRUNCATE 대상에 함께 명시해야
        # 한다(assignments는 위에서 비어있음을 확인했으므로 안전).
        cur.execute("TRUNCATE TABLE combination_pool, assignments")
        # 대량 COPY 동안 유니크 인덱스 유지 비용을 피하기 위해 적재 후 재생성한다.
        cur.execute(
            f"ALTER TABLE combination_pool DROP CONSTRAINT IF EXISTS {UNIQUE_CONSTRAINT_NAME}"
        )

        count = 0
        with cur.copy("COPY combination_pool (id, numbers, combo_key) FROM STDIN") as copy:
            for combo in generate_survivors():
                count += 1
                copy.write_row((count, list(combo), combo_key(combo)))

        logger.info("COPY 완료: %d개 행. 유니크 인덱스를 재생성합니다.", count)
        cur.execute(
            f"ALTER TABLE combination_pool "
            f"ADD CONSTRAINT {UNIQUE_CONSTRAINT_NAME} UNIQUE (combo_key)"
        )
        cur.execute("ANALYZE combination_pool")
        raw_conn.commit()
        return count
    except Exception:
        raw_conn.rollback()
        raise
    finally:
        raw_conn.close()
