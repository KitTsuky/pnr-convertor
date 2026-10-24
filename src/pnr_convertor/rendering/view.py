"""Presentation model: an itinerary as the words and numbers a traveller reads."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from pnr_convertor.domain.geo import KM_PER_MILE
from pnr_convertor.domain.itinerary import Connection, EnrichedSegment, Itinerary, Journey
from pnr_convertor.domain.models import (
    Contact,
    Passenger,
    SeatAssignment,
    SegmentStatusCategory,
    Ticket,
)
from pnr_convertor.domain.reference import Airport

_PASSENGER_TYPES = {
    "ADT": "Adult",
    "CHD": "Child",
    "CNN": "Child",
    "INF": "Infant",
    "INS": "Infant with seat",
    "YTH": "Youth",
    "SRC": "Senior",
    "MIL": "Military",
    "GOV": "Government",
}

# Spelled out so the output never depends on the server's locale.
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

_STATUS_LABELS = {
    SegmentStatusCategory.CONFIRMED: "Confirmed",
    SegmentStatusCategory.WAITLISTED: "Waitlisted",
    SegmentStatusCategory.REQUESTED: "Requested",
    SegmentStatusCategory.CANCELLED: "Cancelled",
}


@dataclass(frozen=True, slots=True)
class PassengerView:
    number: int
    name: str
    type: str
    infant: str | None


@dataclass(frozen=True, slots=True)
class StopView:
    """`place` is the city and code, e.g. `London (LHR)`; `airport` its full name if known."""

    place: str
    airport: str | None
    time: str


@dataclass(frozen=True, slots=True)
class FlightView:
    flight: str
    airline: str
    operated_by: str | None
    booking_class: str
    status: str
    departure: StopView
    arrival: StopView
    duration: str | None
    distance: str | None
    seats: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class JourneyView:
    """`connections[i]` is the wait between `flights[i]` and `flights[i + 1]`."""

    title: str
    date: str
    stops: str
    duration: str | None
    distance: str | None
    flights: tuple[FlightView, ...]
    connections: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TicketView:
    number: str
    passenger: str | None
    issued: str | None


@dataclass(frozen=True, slots=True)
class ItineraryView:
    record_locator: str | None
    passengers: tuple[PassengerView, ...]
    journeys: tuple[JourneyView, ...]
    cancelled: tuple[FlightView, ...]
    tickets: tuple[TicketView, ...]
    contacts: tuple[str, ...]


def build_view(itinerary: Itinerary) -> ItineraryView:
    pnr = itinerary.pnr
    names = {p.index: _name(p) for p in pnr.passengers}
    flights = {
        s.segment.index: _flight(
            s, [seat for seat in pnr.seats if seat.segment_index == s.segment.index], names
        )
        for s in itinerary.segments
    }
    in_journeys = {s.segment.index for j in itinerary.journeys for s in j.segments}
    return ItineraryView(
        record_locator=pnr.record_locator,
        passengers=tuple(_passenger(p) for p in pnr.passengers),
        journeys=tuple(_journey(j, flights) for j in itinerary.journeys),
        cancelled=tuple(
            flights[s.segment.index]
            for s in itinerary.segments
            if s.segment.index not in in_journeys
        ),
        tickets=tuple(_ticket(t, names) for t in pnr.tickets),
        contacts=tuple(_contact(c) for c in pnr.contacts),
    )


def _name(passenger: Passenger) -> str:
    title = f" {passenger.title}" if passenger.title else ""
    return f"{passenger.last_name}/{passenger.first_name}{title}"


def _passenger(passenger: Passenger) -> PassengerView:
    infant = passenger.infant
    infant_text = None
    if infant is not None:
        born = f", born {_day(infant.date_of_birth)}" if infant.date_of_birth else ""
        infant_text = f"{infant.last_name}/{infant.first_name}{born}"
    return PassengerView(
        number=passenger.index,
        name=_name(passenger),
        type=_PASSENGER_TYPES.get(passenger.type_code, passenger.type_code),
        infant=infant_text,
    )


def _flight(
    enriched: EnrichedSegment, seats: Iterable[SeatAssignment], names: dict[int, str]
) -> FlightView:
    segment = enriched.segment
    return FlightView(
        flight=f"{segment.carrier} {segment.flight_number}",
        airline=enriched.airline.name if enriched.airline else segment.carrier,
        operated_by=segment.operated_by,
        booking_class=segment.booking_class,
        status=_status(enriched),
        departure=_stop(segment.origin, enriched.origin, segment.departure),
        arrival=_stop(segment.destination, enriched.destination, segment.arrival),
        duration=_duration(enriched.duration),
        distance=_distance(enriched.distance_km),
        seats=tuple(_seat(seat, names) for seat in seats),
    )


def _status(enriched: EnrichedSegment) -> str:
    status = enriched.segment.status
    label = _STATUS_LABELS.get(status.category)
    return label or status.description or status.code


def _stop(code: str, airport: Airport | None, local: datetime) -> StopView:
    return StopView(
        place=_place(code, airport),
        airport=airport.name if airport else None,
        time=_datetime(local),
    )


def _place(code: str, airport: Airport | None) -> str:
    return f"{airport.city} ({code})" if airport and airport.city else code


def _seat(seat: SeatAssignment, names: dict[int, str]) -> str:
    holder = names.get(seat.passenger_index) if seat.passenger_index else None
    return f"{seat.seat} {holder}" if holder else seat.seat


def _journey(journey: Journey, flights: dict[int, FlightView]) -> JourneyView:
    first, last = journey.segments[0], journey.segments[-1]
    connections = journey.connections
    return JourneyView(
        title=f"{_place(first.segment.origin, first.origin)} to "
        f"{_place(last.segment.destination, last.destination)}",
        date=_date(first.segment.departure.date()),
        stops=_stops(connections),
        duration=_duration(journey.duration),
        distance=_distance(journey.distance_km),
        flights=tuple(flights[s.segment.index] for s in journey.segments),
        connections=tuple(
            _connection(c, s) for c, s in zip(connections, journey.segments[1:], strict=True)
        ),
    )


def _stops(connections: tuple[Connection, ...]) -> str:
    # One segment may still land on the way (a technical stop): "direct", never "nonstop".
    if not connections:
        return "Direct"
    airports = ", ".join(c.airport for c in connections)
    count = len(connections)
    return f"{count} connection{'s' if count > 1 else ''} ({airports})"


def _connection(connection: Connection, onward: EnrichedSegment) -> str:
    place = _place(connection.airport, onward.origin)
    wait = _duration(connection.duration)
    return f"Connection in {place}: {wait}" if wait else f"Connection in {place}"


def _ticket(ticket: Ticket, names: dict[int, str]) -> TicketView:
    holder = names.get(ticket.passenger_index) if ticket.passenger_index else None
    if holder and ticket.infant:
        holder = f"infant of {holder}"
    return TicketView(
        number=ticket.number,
        passenger=holder,
        issued=_day(ticket.issue_date) if ticket.issue_date else None,
    )


def _contact(contact: Contact) -> str:
    return f"{contact.kind.value.capitalize()}: {contact.text}"


def _day(value: date) -> str:
    return f"{value.day:02d} {_MONTHS[value.month - 1]} {value.year}"


def _date(value: date) -> str:
    return f"{_WEEKDAYS[value.weekday()]} {_day(value)}"


def _datetime(value: datetime) -> str:
    return f"{_date(value.date())} {value:%H:%M}"


def _duration(value: timedelta | None) -> str | None:
    if value is None:
        return None
    hours, minutes = divmod(int(value.total_seconds() // 60), 60)
    return f"{hours}h {minutes:02d}m" if hours else f"{minutes}m"


def _distance(km: float | None) -> str | None:
    if km is None:
        return None
    return f"{round(km):,} km ({round(km / KM_PER_MILE):,} mi)"
