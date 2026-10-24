from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime, timedelta

from pnr_convertor.domain.models import (
    Contact,
    ContactKind,
    FlightSegment,
    GdsFormat,
    Infant,
    ParsedPnr,
    ParseWarning,
    Passenger,
    SeatAssignment,
    SegmentStatus,
    Ticket,
)
from pnr_convertor.parsing.amadeus import patterns
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.dates import (
    PAST_TOLERANCE,
    parse_day_month,
    parse_full_date,
    parse_time,
    resolve_date,
)
from pnr_convertor.parsing.text import operating_carrier


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
        tickets: list[Ticket] = []
        seats: list[SeatAssignment] = []
        contacts: list[Contact] = []
        # Segments are chronological, so each one anchors the year of the next.
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
            elif patterns.NAMES_LINE.match(line):
                passengers.extend(_build_passengers(line))
            elif ticket_match := patterns.TICKET.match(line):
                try:
                    tickets.append(_build_ticket(ticket_match))
                except ValueError as exc:
                    warnings.append(ParseWarning(line_number, f"Skipped ticket: {exc}"))
            elif seat_match := patterns.SEAT_REQUEST.match(line):
                seats.extend(_build_seats(seat_match))
            elif contact_match := patterns.CONTACT.match(line):
                contacts.append(_build_contact(contact_match))

        # Elements without a passenger reference belong to the only passenger, if there is one.
        sole_passenger = passengers[0].index if len(passengers) == 1 else None
        return ParsedPnr(
            gds=self.gds,
            record_locator=header.group("locator") if header else None,
            passengers=tuple(passengers),
            segments=tuple(segments),
            warnings=tuple(warnings),
            tickets=tuple(
                replace(t, passenger_index=t.passenger_index or sole_passenger) for t in tickets
            ),
            seats=tuple(
                replace(s, passenger_index=s.passenger_index or sole_passenger) for s in seats
            ),
            contacts=tuple(contacts),
        )


def _build_segment(match: re.Match[str], *, not_before: date, is_first: bool) -> FlightSegment:
    departure_date = resolve_date(
        *parse_day_month(match["departure_date"]),
        not_before=not_before,
        weekday=int(match["weekday"]) if match["weekday"] else None,
        allow_earlier=is_first,
    )
    departure = datetime.combine(departure_date, parse_time(match["departure_time"]))
    arrival = datetime.combine(
        _arrival_date(match, departure_date), parse_time(match["arrival_time"])
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
    passengers = []
    for match in patterns.NAME.finditer(line):
        passenger = Passenger(
            index=int(match["index"]),
            last_name=match["last_name"].strip(),
            first_name=match["first_name"].strip(),
            title=match["title"] or match["spaced_title"],
        )
        passengers.append(_apply_qualifier(passenger, match["qualifier"]))
    return passengers


def _apply_qualifier(passenger: Passenger, qualifier: str | None) -> Passenger:
    if not qualifier:
        return passenger
    if infant := patterns.LAP_INFANT.fullmatch(qualifier):
        return replace(
            passenger,
            infant=Infant(
                last_name=(infant["last_name"] or passenger.last_name).strip(),
                first_name=infant["first_name"].strip(),
                date_of_birth=_optional_date(infant["date_of_birth"]),
            ),
        )
    if typed := patterns.TYPED_PASSENGER.fullmatch(qualifier):
        return replace(
            passenger,
            type_code=typed["type_code"],
            date_of_birth=_optional_date(typed["date_of_birth"]),
        )
    return passenger


def _optional_date(token: str | None) -> date | None:
    if token is None:
        return None
    try:
        return parse_full_date(token)
    except ValueError:
        return None


def _build_ticket(match: re.Match[str]) -> Ticket:
    return Ticket(
        number=match["number"],
        passenger_index=int(match["passenger"]) if match["passenger"] else None,
        issuing_airline=match["airline"],
        issue_date=parse_full_date(match["issue_date"]) if match["issue_date"] else None,
        electronic=match["electronic"] is not None,
        infant=match["holder"] == "INF",
    )


def _build_seats(match: re.Match[str]) -> list[SeatAssignment]:
    return [
        SeatAssignment(
            segment_index=int(match["segment"]),
            passenger_index=int(seat["passenger"]) if seat["passenger"] else None,
            seat=seat["seat"],
        )
        for seat in patterns.SEAT.finditer(match["seats"])
    ]


def _build_contact(match: re.Match[str]) -> Contact:
    text = match["text"]
    is_email = match["qualifier"] == "E" or "@" in text
    return Contact(kind=ContactKind.EMAIL if is_email else ContactKind.PHONE, text=text)
