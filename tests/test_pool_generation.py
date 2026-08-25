from app.services.combination_generator import generate_survivors

EXPECTED_SURVIVOR_COUNT = 3_570_443


def test_full_filter_pass_yields_expected_survivor_count() -> None:
    """검증①: 8,145,060개 전체 조합 중 9개 필터를 통과하는 조합이 정확히
    3,570,443개여야 한다. 전체 C(45,6)를 순회하므로 다른 테스트보다 느리다
    (수십 초)."""
    count = sum(1 for _ in generate_survivors())
    assert count == EXPECTED_SURVIVOR_COUNT
