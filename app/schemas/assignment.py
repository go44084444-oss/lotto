from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CombinationOut(BaseModel):
    id: int
    numbers: list[int]


class AssignmentBatchOut(BaseModel):
    weekly_cycle_id: int
    cycle_key: date
    quota: int
    combinations: list[CombinationOut]


class WinCheckResultItem(BaseModel):
    combination_id: int
    numbers: list[int]
    match_count: int
    matched_bonus: bool
    rank: int | None  # 1~5등, None=낙첨


class WinCheckResponse(BaseModel):
    cycle_key: date
    draw_no: int
    winning_numbers: list[int]
    bonus_no: int
    results: list[WinCheckResultItem]


class WeeklyCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cycle_key: date
    starts_at: datetime
    ends_at: datetime | None
    associated_draw_no: int | None


class WeeklyCycleLinkDrawIn(BaseModel):
    draw_no: int
