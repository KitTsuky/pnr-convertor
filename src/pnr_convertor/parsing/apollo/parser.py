from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime, timedelta

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
from pnr_convertor.parsing.apollo import patterns
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import (
    PAST_TOLERANCE,
    parse_12h,
    parse_day_month,
    parse_full_date,
    resolve_date,
)
from pnr_convertor.parsing.text import operating_carrier
from pnr_convertor.parsing.travelport import read_electronic_tickets


class ApolloParser:
    @property
    def gds(self) -> GdsFormat:
        return GdsFormat.APOLLO

    def detect(self, text: str) -> float:
        if not any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.0
        return 1.0 if patterns.HEADER.search(text) else 0.7

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        header = patterns.HEADER.search(text)
        passengers: list[Passenger] = []
        segments: list[FlightSegment] = []
        contacts: list[Contact] = []
        warnings: list[ParseWarning] = []
        field: str | None = None
        not_before = context.reference_date - PAST_TOLERANCE

        for line_number, line in enumerate(text.splitlines(), start=1):
            if segments and (operator := operating_carrier(line)):
                segments[-1] = replace(segments[-1], operated_by=operator)
                continue
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
                continue

            if field_match := patterns.FIELD.match(line):
                field = field_match["tag"]
                text_value = field_match["rest"].strip()
            elif field is not None and (item := patterns.NUMBERED_ITEM.match(line)):
                text_value = item["text"]
            else:
                field = None
                passengers.extend(_build_passengers(line))
                continue

            if field == "FONE" and text_value:
                contacts.append(Contact(kind=ContactKind.PHONE, text=text_value))

        return ParsedPnr(
            gds=self.gds,
            record_locator=header["locator"] if header else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
            contacts=tuple(contacts),
            tickets=read_electronic_tickets(text, passengers),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    weekdays = patterns.WEEKDAY_PAIR.search(match["indicators"])
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=patterns.WEEKDAYS[weekdays["departure"]] if weekdays else None,
        allow_earlier=is_first,
    )
    arrival_date = departure_date + timedelta(days=_arrival_day_offset(match["day_offset"]))
    return FlightSegment(
        index=int(match["index"]),
        carrier=match["carrier"],
        flight_number=match["flight"],
        booking_class=match["booking_class"],
        origin=match["origin"],
        destination=match["destination"],
        departure=datetime.combine(departure_date, parse_12h(match["departure_time"])),
        arrival=datetime.combine(arrival_date, parse_12h(match["arrival_time"])),
        status=SegmentStatus(match["status"]),
        passenger_count=int(match["passenger_count"]),
    )


def _arrival_day_offset(marker: str | None) -> int:
    if not marker:
        return 0
    days = int(marker[1:]) if len(marker) > 1 else 1
    return -days if marker[0] == "-" else days


def _build_passengers(line: str) -> list[Passenger]:
    passengers = []
    for item in patterns.NAME_ITEM.finditer(line):
        given = patterns.GIVEN_NAME.match(item["given"].strip())
        if given is None:
            continue
        suffix = item["suffix"] or ""
        passengers.append(
            Passenger(
                index=int(item["index"]),
                last_name=item["surname"].strip(),
                first_name=given["first_name"],
                title=given["title"],
                type_code="INF" if item["infant"] else _type_code(suffix),
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
