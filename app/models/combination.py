from sqlalchemy import ARRAY, BigInteger, Integer, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CombinationPool(Base):
    """9개 필터를 통과한 조합 풀(~357만 개). 불변 참조 데이터 — 한 번 적재된 뒤에는
    수정하지 않는다. `draws` 테이블을 절대 참조하지 않는다(과거 당첨 조합 제외 로직 없음)."""

    __tablename__ = "combination_pool"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    numbers: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)
    combo_key: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
