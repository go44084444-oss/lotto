"""배정된 조합과 실제 당첨번호를 비교해 등수를 계산한다. 표준 로또 6/45 등수 규칙:
6개 일치=1등, 5개+보너스=2등, 5개=3등, 4개=4등, 3개=5등, 그 외 낙첨."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WinResult:
    combination_id: int
    numbers: list[int]
    match_count: int
    matched_bonus: bool
    rank: int | None


def _rank(match_count: int, matched_bonus: bool) -> int | None:
    if match_count == 6:
        return 1
    if match_count == 5 and matched_bonus:
        return 2
    if match_count == 5:
        return 3
    if match_count == 4:
        return 4
    if match_count == 3:
        return 5
    return None


def check(
    combination_id: int, numbers: list[int], winning_numbers: list[int], bonus_no: int
) -> WinResult:
    winning_set = set(winning_numbers)
    match_count = sum(1 for n in numbers if n in winning_set)
    matched_bonus = bonus_no in numbers
    return WinResult(
        combination_id=combination_id,
        numbers=sorted(numbers),
        match_count=match_count,
        matched_bonus=matched_bonus,
        rank=_rank(match_count, matched_bonus),
    )
