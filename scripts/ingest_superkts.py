"""1단계 방법 A: superkts.com 엑셀로 1~1234회 당첨번호를 일괄 수집한다.

실행: uv run python -m scripts.ingest_superkts

주의:
- 다운로드 페이지(https://superkts.com/lotto/download)는 HTML만 반환한다.
  실제 파일은 하위의 download_excel.php 엔드포인트에서 받아야 한다.
- 엑셀에는 추첨일자 컬럼이 없다. 로또 6/45는 1회(2002-12-07)부터 매주 토요일
  빠짐없이 추첨되어 왔으므로(1237회=2026-08-15로 검증됨), 추첨일은
  `2002-12-07 + 7 * (draw_no - 1)`일로 결정적으로 계산한다.
- 1~1234회만 이 소스로 적재한다(스펙 범위). 그 이후 회차는 ingest_dhlottery.py가 담당.
"""

from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta

import httpx
import openpyxl
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.draw import Draw

logger = logging.getLogger(__name__)

DOWNLOAD_URL = "https://superkts.com/lotto/download_excel.php"
REFERER = "https://superkts.com/lotto/download"
FIRST_DRAW_DATE = date(2002, 12, 7)
MAX_DRAW_NO = 1234
SOURCE = "superkts_xlsx"


def draw_date_for(draw_no: int) -> date:
    return FIRST_DRAW_DATE + timedelta(weeks=draw_no - 1)


def fetch_workbook_rows() -> list[tuple]:
    resp = httpx.get(
        DOWNLOAD_URL,
        headers={"User-Agent": "Mozilla/5.0", "Referer": REFERER},
        timeout=30,
        follow_redirects=True,
    )
    resp.raise_for_status()
    if not resp.content.startswith(b"PK"):
        raise RuntimeError(
            "다운로드 응답이 xlsx(zip) 형식이 아닙니다. superkts.com 페이지 구조가 "
            "바뀌었을 수 있으니 다운로드 URL을 다시 확인하세요."
        )

    import io

    wb = openpyxl.load_workbook(io.BytesIO(resp.content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=2, values_only=True))  # 1행은 헤더
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    rows = fetch_workbook_rows()
    logger.info("엑셀에서 %d개 행을 읽었습니다.", len(rows))

    records = []
    for row in rows:
        draw_no = row[0]
        if draw_no is None or not (1 <= int(draw_no) <= MAX_DRAW_NO):
            continue
        draw_no = int(draw_no)
        n1, n2, n3, n4, n5, n6, bonus = (int(x) for x in row[1:8])
        records.append(
            {
                "draw_no": draw_no,
                "n1": n1,
                "n2": n2,
                "n3": n3,
                "n4": n4,
                "n5": n5,
                "n6": n6,
                "bonus_no": bonus,
                "draw_date": draw_date_for(draw_no),
                "source": SOURCE,
            }
        )

    if not records:
        logger.warning("적재할 레코드가 없습니다.")
        return

    with SessionLocal() as db:
        stmt = insert(Draw).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["draw_no"])
        result = db.execute(stmt)
        db.commit()
        logger.info(
            "%d개 회차 중 %d개 신규 삽입(기존 회차는 건너뜀).",
            len(records),
            result.rowcount,
        )


if __name__ == "__main__":
    main()
