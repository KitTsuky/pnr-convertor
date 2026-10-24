from __future__ import annotations

import re
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

_DAY_MONTH = re.compile(r"(?P<day>\d{1,2})(?P<month>[A-Z]{3})")

# A PNR may be displayed after its first flight departed; don't jump those dates a year ahead.
PAST_TOLERANCE = timedelta(days=30)

# 29FEB: the next leap year can be up to 8 years away.
_MAX_YEARS_AHEAD = 8

# A day/month falls on a different weekday in each of four consecutive years, so looking two
# years back stays unambiguous.
_MAX_LOOKBACK = timedelta(days=2 * 366)


def parse_day_month(token: str) -> tuple[int, int]:
    """Parse `15MAR` or `5DEC` into `(day, month)`."""
    match = _DAY_MONTH.fullmatch(token)
    if match is None or not 1 <= int(match["day"]) <= 31:
        raise ValueError(f"Malformed GDS date {token!r}")
    month = MONTHS.get(match["month"])
    if month is None:
        raise ValueError(f"Unknown month in GDS date {token!r}")
    return int(match["day"]), month


def parse_full_date(token: str) -> date:
    """Parse a date with a two-digit year, e.g. `30MAR25`."""
    if len(token) != 7 or not token[5:].isdigit():
        raise ValueError(f"Malformed GDS date {token!r}")
    day, month = parse_day_month(token[:5])
    return date(2000 + int(token[5:]), month, day)


def resolve_date(
    day: int,
    month: int,
    *,
    not_before: date,
    weekday: int | None = None,
    allow_earlier: bool = False,
) -> date:
    """Earliest date on or after `not_before`, unless `weekday` (ISO, Monday=1) points elsewhere.

    The weekday picks between this and the next occurrence, or one of the previous two years
    when `allow_earlier` is set (an old PNR displayed today).
    """
    occurrences = _occurrences(
        day, month, not_before.year - 3, not_before.year + _MAX_YEARS_AHEAD + 1
    )
    upcoming = [candidate for candidate in occurrences if candidate >= not_before]
    if not upcoming:
        raise ValueError(f"Day {day} does not exist in month {month}")
    if weekday is None:
        return upcoming[0]

    candidates = upcoming[:2]
    if allow_earlier:
        earliest = not_before - _MAX_LOOKBACK
        candidates += [c for c in occurrences if earliest <= c < not_before]
    return next((c for c in candidates if c.isoweekday() == weekday), upcoming[0])


def resolve_past_date(day: int, month: int, *, not_after: date) -> date:
    """Latest date on or before `not_after`, e.g. a ticket issue date shown without a year."""
    past = [
        c for c in _occurrences(day, month, not_after.year - 4, not_after.year) if c <= not_after
    ]
    if not past:
        raise ValueError(f"Day {day} does not exist in month {month}")
    return past[-1]


def _occurrences(day: int, month: int, first_year: int, last_year: int) -> list[date]:
    occurrences = []
    for year in range(first_year, last_year + 1):
        try:
            occurrences.append(date(year, month, day))
        except ValueError:
            continue
    return occurrences


def parse_hhmm(token: str) -> time:
    if len(token) != 4 or not token.isdigit():
        raise ValueError(f"Malformed GDS time {token!r}")
    return time(int(token[:2]), int(token[2:]))


def parse_time(token: str) -> time:
    """Parse either a 24-hour (`1415`) or a 12-hour (`215P`) GDS time."""
    return parse_12h(token) if token[-1:].isalpha() else parse_hhmm(token)


def parse_12h(token: str) -> time:
    """Parse `945A`, `1229P`, `1200N` (noon) or `1200M` (midnight)."""
    digits, suffix = token[:-1], token[-1]
    if not 3 <= len(digits) <= 4 or not digits.isdigit() or suffix not in "APNM":
        raise ValueError(f"Malformed GDS time {token!r}")
    hour, minute = int(digits[:-2]), int(digits[-2:])
    if not 1 <= hour <= 12:
        raise ValueError(f"Malformed GDS time {token!r}")
    if suffix in "NM":
        if (hour, minute) != (12, 0):
            raise ValueError(f"Malformed GDS time {token!r}")
        return time(12 if suffix == "N" else 0)
    return time(hour % 12 + (12 if suffix == "P" else 0), minute)
