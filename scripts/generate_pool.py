"""2단계: combination_pool을 생성/재생성한다.

실행: uv run python -m scripts.generate_pool
"""

from __future__ import annotations

import logging

from app.services.combination_generator import load_pool

EXPECTED_COUNT = 3_645_902


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    count = load_pool()
    logger.info("생존 조합 %d개를 적재했습니다.", count)

    if count != EXPECTED_COUNT:
        logger.warning(
            "예상 값(%d)과 다릅니다(%d). 필터 로직을 재검토하세요.", EXPECTED_COUNT, count
        )


if __name__ == "__main__":
    main()
