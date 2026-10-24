from __future__ import annotations

from datetime import UTC, date, datetime


class SystemClock:
    def today(self) -> date:
        return datetime.now(UTC).date()
