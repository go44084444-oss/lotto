"""9개 조합 필터 규칙.

중요: 이 필터는 당첨 확률을 높이지 않는다. "패턴이 뚜렷해 보이는" 조합을 판매 풀에서
제외할 뿐이며, 45개 중 6개를 고르는 모든 조합은 여전히 동일한 확률을 가진다. 이
모듈이나 이를 사용하는 API 문서/주석에 "확률을 향상시킨다"는 식의 표현을 쓰지 않는다.

각 함수는 정렬된 6개 숫자 튜플을 받아 해당 규칙에 "해당하면"(=제외 대상이면) True를
반환한다. `passes_all_filters`는 9개 규칙 중 어느 것에도 해당하지 않을 때만 True.
"""

from __future__ import annotations

from collections import Counter

Combo = tuple[int, int, int, int, int, int]

PRIMES_1_45: frozenset[int] = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43})

ZONES: tuple[tuple[int, int], ...] = ((1, 15), (16, 30), (31, 45))

TENS_GROUPS: tuple[tuple[int, int], ...] = ((1, 9), (10, 19), (20, 29), (30, 39), (40, 45))


def is_consecutive(nums: Combo) -> bool:
    """규칙1: 정렬 시 인접한 두 숫자의 차이가 1인 경우가 하나라도 있으면 True."""
    return any(b - a == 1 for a, b in zip(nums, nums[1:]))


def is_all_same_parity(nums: Combo) -> bool:
    """규칙2: 전부 홀수 또는 전부 짝수."""
    return all(n % 2 == 0 for n in nums) or all(n % 2 == 1 for n in nums)


def is_arithmetic_sequence(nums: Combo) -> bool:
    """규칙3: 정렬 시 모든 인접 차이가 동일(등차수열)."""
    diffs = {b - a for a, b in zip(nums, nums[1:])}
    return len(diffs) == 1


def is_zone_clustered(nums: Combo) -> bool:
    """규칙4: 1~15 / 16~30 / 31~45 세 구간 중 한 구간에 6개가 모두 몰림."""
    return any(all(lo <= n <= hi for n in nums) for lo, hi in ZONES)


def is_all_multiples_of_3(nums: Combo) -> bool:
    """규칙5: 3의 배수로만 구성."""
    return all(n % 3 == 0 for n in nums)


def is_all_primes(nums: Combo) -> bool:
    """규칙6: 소수로만 구성."""
    return all(n in PRIMES_1_45 for n in nums)


def has_last_digit_collision(nums: Combo) -> bool:
    """규칙7: 1의 자리 숫자가 같은 게 4개 이상."""
    counts = Counter(n % 10 for n in nums)
    return max(counts.values()) >= 4


def has_tens_group_collision(nums: Combo) -> bool:
    """규칙8: 십의 자리 그룹이 같은 게 5개 이상(스펙 본문 기준 임계값)."""

    def group_index(n: int) -> int:
        for i, (lo, hi) in enumerate(TENS_GROUPS):
            if lo <= n <= hi:
                return i
        raise ValueError(f"1~45 범위를 벗어난 숫자: {n}")

    counts = Counter(group_index(n) for n in nums)
    return max(counts.values()) >= 5


def has_ticket_grid_collision(nums: Combo) -> bool:
    """규칙9: 실제 로또 구매 용지의 7칸 가로 배열 기준으로, 같은 행 또는 같은 열에
    4개 이상 몰리면 True. 행 = (숫자-1)//7, 열 = (숫자-1)%7
    (1행:1-7, 2행:8-14, 3행:15-21, 4행:22-28, 5행:29-35, 6행:36-42, 7행:43-45)."""
    rows = Counter((n - 1) // 7 for n in nums)
    cols = Counter((n - 1) % 7 for n in nums)
    return max(rows.values()) >= 4 or max(cols.values()) >= 4


ALL_RULES = (
    is_consecutive,
    is_all_same_parity,
    is_arithmetic_sequence,
    is_zone_clustered,
    is_all_multiples_of_3,
    is_all_primes,
    has_last_digit_collision,
    has_tens_group_collision,
    has_ticket_grid_collision,
)


def passes_all_filters(nums: Combo) -> bool:
    """9개 규칙 중 어느 것에도 해당하지 않으면(=제외되지 않으면) True."""
    return not any(rule(nums) for rule in ALL_RULES)
