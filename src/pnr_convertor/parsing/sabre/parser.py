from __future__ import annotations

import re
from datetime import date, datetime

from pnr_convertor.domain.models import (
    FlightSegment,
    GdsFormat,
    ParsedPnr,
    ParseWarning,
    SegmentStatus,
)
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import PAST_TOLERANCE, parse_12h, parse_day_month, resolve_date
from pnr_convertor.parsing.sabre import patterns


class SabreParser:
    @property
    def gds(self) -> GdsFormat:
        return GdsFormat.SABRE

    def detect(self, text: str) -> float:
        # Letter weekdays and 12-hour times make a segment line distinctive on its own.
        if any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.9
        return 0.0

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        segments: list[FlightSegment] = []
        warnings: list[ParseWarning] = []
        not_before = context.reference_date - PAST_TOLERANCE

        for line_number, line in enumerate(text.splitlines(), start=1):
            if segment_match := patterns.AIR_SEGMENT.match(line):
                try:
                    segment = _build_segment(
                        segment_match, not_before=not_before, is_first=not segments
                    )
                except ValueError as exc:
                    warnings.append(ParseWarning(line_number, f"Skipped air segment: {exc}"))
                    continue
                segments.append(segment)
                not_before = segment.departure.date()

        return ParsedPnr(
            gds=self.gds,
            record_locator=None,
            passengers=(),
            segments=tuple(segments),
            warnings=tuple(warnings),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=patterns.WEEKDAYS[match["weekday"]],
        allow_earlier=is_first,
    )
    departure = datetime.combine(departure_date, parse_12h(match["departure_time"]))
    arrival = datetime.combine(
        _arrival_date(match, departure_date), parse_12h(match["arrival_time"])
    )
    return FlightSegment(
        index=int(match["index"]),
        carrier=match["carrier"],
        flight_number=match["flight"],
        booking_class=match["booking_class"],
        origin=match["origin"],
        destination=match["destination"],
        departure=departure,
        arrival=arrival,
        status=SegmentStatus(match["status"]),
        passenger_count=int(match["passenger_count"]),
    )


def _arrival_date(match: re.Match[str], departure_date: date) -> date:
    if not match["arrival_date"]:
        return departure_date
    return resolve_date(
        *parse_day_month(match["arrival_date"]),
        not_before=departure_date,
        weekday=patterns.WEEKDAYS[match["arrival_weekday"]],
    )
