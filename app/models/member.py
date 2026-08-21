from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MembershipTier(Base):
    """배분 개수(quota)를 코드가 아니라 데이터로 관리 — 유료 티어 추가는 행 삽입만으로."""

    __tablename__ = "membership_tiers"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    weekly_quota: Mapped[int] = mapped_column(Integer, nullable=False)
    display_name: Mapped[str] = mapped_column(String(50), nullable=False)


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (CheckConstraint("status IN ('active', 'withdrawn')", name="ck_members_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    tier: Mapped[str] = mapped_column(
        String(20), ForeignKey("membership_tiers.code"), nullable=False, server_default="free"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
