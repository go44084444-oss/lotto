from datetime import date

from pydantic import BaseModel


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
