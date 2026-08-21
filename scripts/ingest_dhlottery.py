"""1단계 방법 B: 동행복권 API로 superkts 엑셀 범위(1~1234회) 이후의 회차를 개별 수집한다.

실행: uv run python -m scripts.ingest_dhlottery [--up-to 1240]

--up-to를 생략하면 오늘 날짜 기준으로 이미 추첨이 끝났을 것으로 추정되는 최신
회차까지 시도한다(1회=2002-12-07, 매주 토요일 추첨 기준 역산).

주의:
- 동행복권 사이트는 자동화된 요청에 "서비스 접근 대기 중입니다" 같은 대기실/차단
  페이지(HTML)를 반환할 수 있다. 이 스크립트는 이런 경우를 우회하려 하지 않고,
  JSON이 아닌 응답을 받으면 즉시 실패로 간주하고 무엇이 왜 실패했는지 로그로
  남긴 뒤 중단한다. 실패 시 운영자가 브라우저로 직접 접근 가능한지, 요청 빈도를
  낮춰야 하는지 등을 확인해야 한다.
- 요청 사이에 딜레이를 두어 과도한 호출을 피한다.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import date, datetime, timedelta

import httpx
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.draw import Draw

logger = logging.getLogger(__name__)

API_URL = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
FIRST_DRAW_DATE = date(2002, 12, 7)
MIN_DRAW_NO = 1235  # superkts 범위(1~1234) 다음부터
SOURCE = "dhlottery_api"
REQUEST_DELAY_SECONDS = 1.0


def estimate_latest_draw_no(today: date | None = None) -> int:
    today = today or date.today()
    weeks_since_first = (today - FIRST_DRAW_DATE).days // 7
    return weeks_since_first + 1


def fetch_draw(client: httpx.Client, draw_no: int) -> dict | None:
    resp = client.get(
        API_URL.format(draw_no=draw_no),
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(
            f"{draw_no}회: JSON이 아닌 응답을 받았습니다(사이트가 차단/대기 페이지를 "
            "반환했을 수 있습니다). 우회를 시도하지 않고 중단합니다. "
            f"Content-Type={resp.headers.get('content-type')}"
        ) from exc

    if data.get("returnValue") != "success":
        return None  # 아직 추첨되지 않은 회차

    return data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--up-to", type=int, default=None, help="마지막으로 시도할 회차 번호")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    up_to = args.up_to or estimate_latest_draw_no()
    logger.info("%d회부터 %d회까지 시도합니다.", MIN_DRAW_NO, up_to)

    inserted = 0
    with httpx.Client() as client, SessionLocal() as db:
        for draw_no in range(MIN_DRAW_NO, up_to + 1):
            try:
                data = fetch_draw(client, draw_no)
            except RuntimeError as exc:
                logger.error(str(exc))
                break

            if data is None:
                logger.info("%d회는 아직 추첨되지 않았습니다. 중단합니다.", draw_no)
                break

            record = {
                "draw_no": data["drwNo"],
                "n1": data["drwtNo1"],
                "n2": data["drwtNo2"],
                "n3": data["drwtNo3"],
                "n4": data["drwtNo4"],
                "n5": data["drwtNo5"],
                "n6": data["drwtNo6"],
                "bonus_no": data["bnusNo"],
                "draw_date": datetime.strptime(data["drwNoDate"], "%Y-%m-%d").date(),
                "source": SOURCE,
            }
            stmt = insert(Draw).values(record)
            stmt = stmt.on_conflict_do_nothing(index_elements=["draw_no"])
            result = db.execute(stmt)
            db.commit()
            inserted += result.rowcount

            time.sleep(REQUEST_DELAY_SECONDS)

    logger.info("%d개 회차를 신규 삽입했습니다.", inserted)


if __name__ == "__main__":
    main()
