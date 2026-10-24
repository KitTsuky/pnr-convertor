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

# A day/month falls on a different weekday in each of four consecutive years, so looking two
# years back stays unambiguous.
_MAX_LOOKBACK = timedelta(days=2 * 366)


def parse_day_month(token: str) -> tuple[int, int]:
    if len(token) != 5 or not token[:2].isdigit():
        raise ValueError(f"Malformed GDS date {token!r}")
    month = MONTHS.get(token[2:])
    if month is None:
        raise ValueError(f"Unknown month in GDS date {token!r}")
    return int(token[:2]), month


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
