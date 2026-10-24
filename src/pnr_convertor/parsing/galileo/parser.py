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
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import (
    PAST_TOLERANCE,
    parse_day_month,
    parse_full_date,
    parse_time,
    resolve_date,
)
from pnr_convertor.parsing.galileo import patterns


class GalileoParser:
    @property
    def gds(self) -> GdsFormat:
        return GdsFormat.GALILEO

    def detect(self, text: str) -> float:
        if patterns.HEADER.search(text):
            return 1.0
        # The dot after the segment number sets Galileo apart from Amadeus and Sabre.
        if any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.8
        return 0.0

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        header = patterns.HEADER.search(text)
        passengers: list[Passenger] = []
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
            else:
                passengers.extend(_build_passengers(line))

        return ParsedPnr(
            gds=self.gds,
            record_locator=header["locator"] if header else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    weekdays = patterns.WEEKDAY_PAIR.search(match["indicators"])
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=patterns.WEEKDAYS[weekdays["departure"]] if weekdays else None,
        allow_earlier=is_first,
    )
    arrival_date = departure_date + timedelta(days=_arrival_day_offset(match))
    return FlightSegment(
        index=int(match["index"]),
        carrier=match["carrier"],
        flight_number=match["flight"],
        booking_class=match["booking_class"],
        origin=match["origin"],
        destination=match["destination"],
        departure=datetime.combine(departure_date, parse_time(match["departure_time"])),
        arrival=datetime.combine(arrival_date, parse_time(match["arrival_time"])),
        status=SegmentStatus(match["status"]),
        passenger_count=int(match["passenger_count"]),
    )


def _arrival_day_offset(match: re.Match[str]) -> int:
    if match["arrival_marker"]:
        return patterns.ARRIVAL_DAY_MARKERS[match["arrival_marker"]]
    if match["day_offset"]:
        return int(match["day_offset"])
    return 0


def _build_passengers(line: str) -> list[Passenger]:
    passengers = []
    for item in patterns.NAME_ITEM.finditer(line):
        given = patterns.GIVEN_NAME.match(item["given"].strip())
        if given is None:
            continue
        suffix = item["suffix"] or ""
        is_infant = item["infant"] is not None
        passengers.append(
            Passenger(
                index=int(item["index"]),
                last_name=item["surname"].strip(),
                first_name=given["first_name"],
                title=given["title"] or given["spaced_title"],
                type_code="INF" if is_infant else _type_code(suffix),
                date_of_birth=_date_of_birth(suffix),
            )
        )
    return passengers


def _type_code(suffix: str) -> str:
    if patterns.PASSENGER_TYPE.fullmatch(suffix):
        return suffix
    if patterns.CHILD_AGE.fullmatch(suffix):
        return "CHD"
    return "ADT"


def _date_of_birth(suffix: str) -> date | None:
    if not patterns.DATE_OF_BIRTH.fullmatch(suffix):
        return None
    try:
        return parse_full_date(suffix)
    except ValueError:
        return None
