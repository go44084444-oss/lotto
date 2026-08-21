from datetime import date, datetime, timedelta

from sqlalchemy import Date, DateTime, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

FIRST_DRAW_DATE = date(2002, 12, 7)


def draw_date_for(draw_no: int) -> date:
    """1회(2002-12-07)부터 매주 토요일 빠짐없이 추첨되어 왔다는 전제로 회차의 추첨일을 계산한다."""
    return FIRST_DRAW_DATE + timedelta(days=7 * (draw_no - 1))


class Draw(Base):
    """과거 당첨번호 — 참고용 데이터. 조합 생성/배분 로직은 이 테이블을 절대 참조하지 않는다."""

    __tablename__ = "draws"

    draw_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    n1: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    n2: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    n3: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    n4: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    n5: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    n6: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bonus_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    draw_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @property
    def numbers(self) -> list[int]:
        return [self.n1, self.n2, self.n3, self.n4, self.n5, self.n6]
