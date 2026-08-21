from app.services import filters

# 1237회(2026-08-15) 실제 당첨번호 — 스펙의 검증③: 8개 필터를 모두 통과해야 한다.
GOOD_COMBO: filters.Combo = (10, 20, 23, 34, 37, 40)


def test_draw_1237_known_good_combo_survives_all_filters() -> None:
    assert filters.passes_all_filters(GOOD_COMBO) is True


class TestIsConsecutive:
    def test_triggers_on_adjacent_pair(self) -> None:
        assert filters.is_consecutive((1, 2, 3, 4, 5, 6)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_consecutive(GOOD_COMBO) is False


class TestIsAllSameParity:
    def test_triggers_on_all_even(self) -> None:
        assert filters.is_all_same_parity((2, 4, 6, 8, 10, 12)) is True

    def test_triggers_on_all_odd(self) -> None:
        assert filters.is_all_same_parity((1, 3, 5, 7, 9, 11)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_all_same_parity(GOOD_COMBO) is False


class TestIsArithmeticSequence:
    def test_triggers_on_constant_step(self) -> None:
        assert filters.is_arithmetic_sequence((3, 9, 15, 21, 27, 33)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_arithmetic_sequence(GOOD_COMBO) is False


class TestIsZoneClustered:
    def test_triggers_when_all_in_one_zone(self) -> None:
        assert filters.is_zone_clustered((1, 2, 3, 4, 5, 15)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_zone_clustered(GOOD_COMBO) is False


class TestIsAllMultiplesOf3:
    def test_triggers_on_all_multiples(self) -> None:
        assert filters.is_all_multiples_of_3((3, 6, 9, 12, 15, 18)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_all_multiples_of_3(GOOD_COMBO) is False


class TestIsAllPrimes:
    def test_triggers_on_all_primes(self) -> None:
        assert filters.is_all_primes((2, 3, 5, 7, 11, 13)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.is_all_primes(GOOD_COMBO) is False


class TestHasLastDigitCollision:
    def test_triggers_when_four_share_units_digit(self) -> None:
        assert filters.has_last_digit_collision((1, 4, 7, 11, 21, 31)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.has_last_digit_collision(GOOD_COMBO) is False


class TestHasTensGroupCollision:
    def test_triggers_when_five_share_tens_group(self) -> None:
        assert filters.has_tens_group_collision((10, 11, 12, 13, 14, 20)) is True

    def test_does_not_trigger_on_known_good_combo(self) -> None:
        assert filters.has_tens_group_collision(GOOD_COMBO) is False
