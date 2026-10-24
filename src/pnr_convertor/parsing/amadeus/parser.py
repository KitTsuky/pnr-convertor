from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from pnr_convertor.domain.models import (
    FlightSegment,
    GdsFormat,
    ParsedPnr,
    ParseWarning,
    Passenger,
    SegmentStatus,
)
from pnr_convertor.parsing.amadeus import patterns
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import PAST_TOLERANCE, parse_day_month, parse_hhmm, resolve_date


class AmadeusParser:
    @property
    def gds(self) -> GdsFormat:
        return GdsFormat.AMADEUS

    def detect(self, text: str) -> float:
        if patterns.HEADER.search(text):
            return 1.0
        if any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.6
        return 0.0

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        header = patterns.HEADER.search(text)
        passengers: list[Passenger] = []
        segments: list[FlightSegment] = []
        warnings: list[ParseWarning] = []
        # Segments are chronological, so each one anchors the year of the next.
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
            elif patterns.NAMES_LINE.match(line):
                passengers.extend(_build_passengers(line))

        return ParsedPnr(
            gds=self.gds,
            record_locator=header.group("locator") if header else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=int(match["weekday"]) if match["weekday"] else None,
        allow_earlier=is_first,
    )
    departure = datetime.combine(departure_date, parse_hhmm(match["departure_time"]))
    arrival = datetime.combine(
        _arrival_date(match, departure_date), parse_hhmm(match["arrival_time"])
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
    if match["arrival_date"]:
        return resolve_date(*parse_day_month(match["arrival_date"]), not_before=departure_date)
    if match["day_offset"]:
        return departure_date + timedelta(days=int(match["day_offset"]))
    return departure_date


def _build_passengers(line: str) -> list[Passenger]:
    return [
        Passenger(
            index=int(match["index"]),
            last_name=match["last_name"].strip(),
            first_name=match["first_name"].strip(),
            title=match["title"],
        )
        for match in patterns.NAME.finditer(line)
    ]
