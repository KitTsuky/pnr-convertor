from __future__ import annotations

import re
from datetime import date, datetime

from pnr_convertor.domain.models import (
    Contact,
    ContactKind,
    FlightSegment,
    GdsFormat,
    ParsedPnr,
    ParseWarning,
    Passenger,
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
        if patterns.SIGNATURE.search(text):
            return 1.0
        # Letter weekdays and 12-hour times make a segment line distinctive on its own.
        if any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.9
        return 0.0

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        signature = patterns.SIGNATURE.search(text)
        passengers: list[Passenger] = []
        segments: list[FlightSegment] = []
        contacts: list[Contact] = []
        warnings: list[ParseWarning] = []
        not_before = context.reference_date - PAST_TOLERANCE
        section: str | None = None

        for line_number, line in enumerate(text.splitlines(), start=1):
            if header := patterns.SECTION_HEADER.match(line):
                section = header["section"]
                continue
            if section == "PHONES":
                if item := patterns.NUMBERED_ITEM.match(line):
                    contacts.append(Contact(kind=ContactKind.PHONE, text=item["text"]))
                    continue
                section = None

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
            elif section is None:
                passengers.extend(_build_passengers(line, first_index=len(passengers) + 1))

        return ParsedPnr(
            gds=self.gds,
            record_locator=signature["locator"] if signature else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
            contacts=tuple(contacts),
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


def _build_passengers(line: str, *, first_index: int) -> list[Passenger]:
    passengers: list[Passenger] = []
    for item in patterns.NAME_ITEM.finditer(line):
        for given in item["given_names"].strip("/").split("/"):
            name = patterns.GIVEN_NAME.match(given.strip())
            if name is None:
                continue
            passengers.append(
                Passenger(
                    index=first_index + len(passengers),
                    last_name=item["surname"].strip(),
                    first_name=name["first_name"],
                    title=name["title"],
                )
            )
    return passengers
