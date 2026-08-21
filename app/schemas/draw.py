from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DrawOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    draw_no: int
    numbers: list[int]
    bonus_no: int
    draw_date: date


class DrawIn(BaseModel):
    """관리자가 당첨번호를 수동으로 입력할 때 쓰는 입력 스키마.

    동행복권 사이트가 자동 요청을 차단할 때, 우회하지 않고 사람이 직접 입력하는
    대체 경로로 쓰인다.
    """

    draw_no: int = Field(..., ge=1, le=32767)
    numbers: list[int]
    bonus_no: int = Field(..., ge=1, le=45)
    draw_date: date | None = None

    @model_validator(mode="after")
    def _validate_numbers(self) -> "DrawIn":
        if len(self.numbers) != 6:
            raise ValueError("numbers는 정확히 6개여야 합니다.")
        if len(set(self.numbers)) != 6:
            raise ValueError("numbers에 중복된 번호가 있습니다.")
        if any(not (1 <= n <= 45) for n in self.numbers):
            raise ValueError("numbers는 1~45 범위여야 합니다.")
        if self.bonus_no in self.numbers:
            raise ValueError("bonus_no는 numbers와 겹칠 수 없습니다.")
        return self
