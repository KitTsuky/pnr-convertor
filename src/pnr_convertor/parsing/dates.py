from __future__ import annotations

from datetime import date, time, timedelta

MONTHS: dict[str, int] = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

# A PNR may be displayed after its first flight departed; don't jump those dates a year ahead.
PAST_TOLERANCE = timedelta(days=30)

# 29FEB: the next leap year can be up to 8 years away.
_MAX_YEARS_AHEAD = 8


def parse_day_month(token: str) -> tuple[int, int]:
    if len(token) != 5 or not token[:2].isdigit():
        raise ValueError(f"Malformed GDS date {token!r}")
    month = MONTHS.get(token[2:])
    if month is None:
        raise ValueError(f"Unknown month in GDS date {token!r}")
    return int(token[:2]), month


def resolve_date(day: int, month: int, *, not_before: date) -> date:
    for year in range(not_before.year, not_before.year + _MAX_YEARS_AHEAD + 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if candidate >= not_before:
            return candidate
    raise ValueError(f"Day {day} does not exist in month {month}")


def parse_hhmm(token: str) -> time:
    if len(token) != 4 or not token.isdigit():
        raise ValueError(f"Malformed GDS time {token!r}")
    return time(int(token[:2]), int(token[2:]))
