from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeeklyCycle(Base):
    """'주'를 1급 개념으로 만들어 리셋 시각을 스케줄러 장애에도 견고하게 처리한다."""

    __tablename__ = "weekly_cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cycle_key: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    associated_draw_no: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("draws.draw_no"), nullable=True
    )


class Assignment(Base):
    """같은 주 내 중복 배정 금지는 UNIQUE(weekly_cycle_id, combination_id)로 DB가 강제한다.
    애플리케이션 로직(assignment_service)은 후보를 고르는 최적화일 뿐, 정합성의 근원이
    아니다."""

    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint("weekly_cycle_id", "combination_id", name="uq_assignment_no_overlap"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    weekly_cycle_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("weekly_cycles.id"), nullable=False
    )
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    combination_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("combination_pool.id"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
