from __future__ import annotations

from datetime import date, time

import pytest

from pnr_convertor.parsing.dates import (
    parse_12h,
    parse_day_month,
    parse_full_date,
    parse_hhmm,
    parse_time,
    resolve_date,
    resolve_past_date,
)


@pytest.mark.parametrize(
    ("token", "expected"),
    [("15MAR", (15, 3)), ("01JAN", (1, 1)), ("31DEC", (31, 12)), ("5DEC", (5, 12))],
)
def test_parse_day_month(token: str, expected: tuple[int, int]) -> None:
    assert parse_day_month(token) == expected


@pytest.mark.parametrize("token", ["15XYZ", "MAR", "AAMAR", "15MARCH", "00MAR", "123MAR"])
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


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("945A", time(9, 45)),
        ("1155A", time(11, 55)),
        ("1229P", time(12, 29)),
        ("1203P", time(12, 3)),
        ("505P", time(17, 5)),
        ("1200A", time(0, 0)),
        ("1200N", time(12, 0)),
        ("1200M", time(0, 0)),
    ],
)
def test_parse_12h(token: str, expected: time) -> None:
    assert parse_12h(token) == expected


@pytest.mark.parametrize("token", ["945", "945X", "1345P", "045A", "960A", "1230N", "A945"])
def test_parse_12h_rejects_invalid(token: str) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - message differs per failure mode
        parse_12h(token)


@pytest.mark.parametrize(("token", "expected"), [("1415", time(14, 15)), ("215P", time(14, 15))])
def test_parse_time_accepts_both_clocks(token: str, expected: time) -> None:
    assert parse_time(token) == expected


def test_parse_full_date() -> None:
    assert parse_full_date("30MAR25") == date(2025, 3, 30)


@pytest.mark.parametrize("token", ["30MAR", "30MAR2025", "30MARXX"])
def test_parse_full_date_rejects_malformed(token: str) -> None:
    with pytest.raises(ValueError, match="Malformed"):
        parse_full_date(token)


@pytest.mark.parametrize(
    ("day", "month", "not_after", "expected"),
    [
        (14, 10, date(2026, 1, 15), date(2025, 10, 14)),
        (15, 1, date(2026, 1, 15), date(2026, 1, 15)),
        (10, 1, date(2026, 1, 15), date(2026, 1, 10)),
        (29, 2, date(2026, 1, 15), date(2024, 2, 29)),
    ],
)
def test_resolve_past_date(day: int, month: int, not_after: date, expected: date) -> None:
    assert resolve_past_date(day, month, not_after=not_after) == expected


def test_resolve_past_date_rejects_impossible_day() -> None:
    with pytest.raises(ValueError, match="does not exist"):
        resolve_past_date(31, 4, not_after=date(2026, 1, 15))
