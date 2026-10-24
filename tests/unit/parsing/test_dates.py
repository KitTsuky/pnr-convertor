from __future__ import annotations

from datetime import date, time

import pytest

from pnr_convertor.parsing.dates import parse_day_month, parse_hhmm, resolve_date


@pytest.mark.parametrize(
    ("token", "expected"),
    [("15MAR", (15, 3)), ("01JAN", (1, 1)), ("31DEC", (31, 12))],
)
def test_parse_day_month(token: str, expected: tuple[int, int]) -> None:
    assert parse_day_month(token) == expected


@pytest.mark.parametrize("token", ["15XYZ", "5MAR", "AAMAR", "15MARCH"])
def test_parse_day_month_rejects_malformed(token: str) -> None:
    with pytest.raises(ValueError, match="GDS date"):
        parse_day_month(token)


@pytest.mark.parametrize(
    ("day", "month", "not_before", "expected"),
    [
        pytest.param(15, 3, date(2026, 1, 1), date(2026, 3, 15), id="later-this-year"),
        pytest.param(5, 1, date(2026, 2, 1), date(2027, 1, 5), id="rolls-into-next-year"),
        pytest.param(1, 2, date(2026, 2, 1), date(2026, 2, 1), id="same-day-inclusive"),
        pytest.param(29, 2, date(2026, 1, 1), date(2028, 2, 29), id="next-leap-year"),
    ],
)
def test_resolve_date(day: int, month: int, not_before: date, expected: date) -> None:
    assert resolve_date(day, month, not_before=not_before) == expected


def test_resolve_date_rejects_impossible_day() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        resolve_date(31, 4, not_before=date(2026, 1, 1))


def test_parse_hhmm() -> None:
    assert parse_hhmm("0710") == time(7, 10)


@pytest.mark.parametrize("token", ["2460", "2500", "710", "07:1"])
def test_parse_hhmm_rejects_invalid(token: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - message differs per failure mode
        parse_hhmm(token)


@pytest.mark.parametrize(
    ("not_before", "weekday", "allow_earlier", "expected"),
    [
        pytest.param(date(2025, 3, 8), 4, False, date(2025, 6, 5), id="matches-upcoming"),
        pytest.param(date(2026, 1, 1), 6, False, date(2027, 6, 5), id="points-to-next-year"),
        pytest.param(date(2026, 9, 15), 4, True, date(2025, 6, 5), id="old-pnr-previous-year"),
        pytest.param(date(2026, 9, 15), 4, False, date(2027, 6, 5), id="no-lookback-when-chained"),
        pytest.param(date(2026, 1, 1), 2, False, date(2026, 6, 5), id="mismatch-falls-back"),
    ],
)
def test_resolve_date_uses_weekday(
    not_before: date, weekday: int, allow_earlier: bool, expected: date
) -> None:
    assert (
        resolve_date(5, 6, not_before=not_before, weekday=weekday, allow_earlier=allow_earlier)
        == expected
    )
