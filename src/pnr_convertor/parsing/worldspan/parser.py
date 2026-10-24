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
    Ticket,
)
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import PAST_TOLERANCE, parse_day_month, parse_time, resolve_date
from pnr_convertor.parsing.worldspan import patterns


class WorldspanParser:
    @property
    def gds(self) -> GdsFormat:
        return GdsFormat.WORLDSPAN

    def detect(self, text: str) -> float:
        if patterns.HEADER.search(text):
            return 1.0
        if any(patterns.AIR_SEGMENT.match(line) for line in text.splitlines()):
            return 0.8
        return 0.0

    def parse(self, text: str, context: ParseContext) -> ParsedPnr:
        header = patterns.HEADER.search(text)
        passengers: list[Passenger] = []
        segments: list[FlightSegment] = []
        contacts: list[Contact] = []
        tickets: list[Ticket] = []
        warnings: list[ParseWarning] = []
        not_before = context.reference_date - PAST_TOLERANCE
        field: str | None = None

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
                continue

            if field_match := patterns.FIELD.match(line):
                field = field_match["tag"]
                item_text = field_match["rest"]
            elif field is not None and (item := patterns.NUMBERED_ITEM.match(line)):
                item_text = line
            else:
                field = None
                passengers.extend(_build_passengers(line))
                continue

            if item := patterns.NUMBERED_ITEM.match(item_text):
                if field == "P":
                    contacts.append(_build_contact(item["text"]))
                elif field == "T" and (ticket := patterns.TICKET.search(item["text"])):
                    tickets.append(_build_ticket(ticket))

        # A ticket line carries no passenger reference; it belongs to the only passenger.
        sole_passenger = passengers[0].index if len(passengers) == 1 else None
        return ParsedPnr(
            gds=self.gds,
            record_locator=header["locator"] if header else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
            tickets=tuple(replace(t, passenger_index=sole_passenger) for t in tickets),
            contacts=tuple(contacts),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=patterns.WEEKDAYS[match["weekday"]],
        allow_earlier=is_first,
    )
    offset = int(match["day_offset"].replace("#", "")) if match["day_offset"] else 0
    return FlightSegment(
        index=int(match["index"]),
        carrier=match["carrier"],
        flight_number=match["flight"],
        booking_class=match["booking_class"],
        origin=match["origin"],
        destination=match["destination"],
        departure=datetime.combine(departure_date, parse_time(match["departure_time"])),
        arrival=datetime.combine(
            departure_date + timedelta(days=offset), parse_time(match["arrival_time"])
        ),
        status=SegmentStatus(match["status"]),
        passenger_count=int(match["passenger_count"]),
    )


def _build_passengers(line: str) -> list[Passenger]:
    passengers = []
    for item in patterns.NAME_ITEM.finditer(line):
        given = patterns.GIVEN_NAME.match(item["given"].strip(" ."))
        if given is None:
            continue
        passengers.append(
            Passenger(
                index=int(item["index"]),
                last_name=item["surname"].strip(),
                first_name=given["first_name"].strip(" ."),
                title=given["title"] or given["dotted_title"],
                type_code=item["type_code"] or "ADT",
            )
        )
    return passengers


def _build_contact(text: str) -> Contact:
    return Contact(kind=ContactKind.EMAIL if "@" in text else ContactKind.PHONE, text=text)


def _build_ticket(match: re.Match[str]) -> Ticket:
    number = match["number"]
    return Ticket(
        number=f"{number[:3]}-{number[3:]}",
        passenger_index=None,
        issuing_airline=None,
        issue_date=None,
        electronic=match["electronic"] is not None,
    )
