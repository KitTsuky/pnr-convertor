"""Public v1 contract. Changing a field here is a breaking change for clients."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from pnr_convertor.domain.geo import KM_PER_MILE
from pnr_convertor.domain.itinerary import Connection, EnrichedSegment, Itinerary, Journey
from pnr_convertor.domain.models import (
    Contact,
    ContactKind,
    GdsFormat,
    Infant,
    ParseWarning,
    Passenger,
    SeatAssignment,
    SegmentStatusCategory,
    Ticket,
)
from pnr_convertor.domain.reference import Airline, Airport

MAX_PNR_LENGTH = 20_000


class OutputFormat(StrEnum):
    JSON = "json"
    TEXT = "text"
    HTML = "html"


def _minutes(duration: timedelta | None) -> int | None:
    return None if duration is None else int(duration.total_seconds() // 60)


class _Schema(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class DistanceOut(_Schema):
    km: int
    miles: int

    @classmethod
    def from_km(cls, km: float | None) -> DistanceOut | None:
        return None if km is None else cls(km=round(km), miles=round(km / KM_PER_MILE))


class ConvertRequest(_Schema):
    pnr: str = Field(
        min_length=1,
        max_length=MAX_PNR_LENGTH,
        description="Raw PNR text exactly as displayed by the GDS terminal.",
    )
    gds: GdsFormat | None = Field(default=None, description="Source format. Omit to auto-detect.")
    reference_date: date | None = Field(
        default=None,
        description=(
            "Date the PNR was displayed; used to infer years for dates like `15MAR`. "
            "Defaults to today (UTC)."
        ),
    )


class InfantOut(_Schema):
    last_name: str
    first_name: str
    date_of_birth: date | None

    @classmethod
    def from_domain(cls, infant: Infant | None) -> InfantOut | None:
        if infant is None:
            return None
        return cls(
            last_name=infant.last_name,
            first_name=infant.first_name,
            date_of_birth=infant.date_of_birth,
        )


class PassengerOut(_Schema):
    index: int
    last_name: str
    first_name: str
    title: str | None
    type: str = Field(description="GDS passenger type: ADT, CHD, INS (infant with a seat), ...")
    date_of_birth: date | None
    infant: InfantOut | None = Field(description="Infant travelling on this passenger's lap.")

    @classmethod
    def from_domain(cls, passenger: Passenger) -> PassengerOut:
        return cls(
            index=passenger.index,
            last_name=passenger.last_name,
            first_name=passenger.first_name,
            title=passenger.title,
            type=passenger.type_code,
            date_of_birth=passenger.date_of_birth,
            infant=InfantOut.from_domain(passenger.infant),
        )


class AirportOut(_Schema):
    iata: str
    name: str
    city: str | None
    country: str = Field(description="ISO 3166-1 alpha-2 country code.")
    timezone: str = Field(description="IANA timezone, e.g. `Europe/Bucharest`.")
    latitude: float
    longitude: float

    @classmethod
    def from_domain(cls, airport: Airport | None) -> AirportOut | None:
        if airport is None:
            return None
        return cls(
            iata=airport.iata,
            name=airport.name,
            city=airport.city,
            country=airport.country,
            timezone=airport.timezone,
            latitude=airport.latitude,
            longitude=airport.longitude,
        )


class AirlineOut(_Schema):
    iata: str
    name: str
    logo_url: str | None = Field(description="Path of the airline's PNG logo; null if none.")

    @classmethod
    def from_domain(cls, airline: Airline | None) -> AirlineOut | None:
        if airline is None:
            return None
        logo_url = f"/v1/airlines/{airline.iata}/logo" if airline.has_logo else None
        return cls(iata=airline.iata, name=airline.name, logo_url=logo_url)


class SeatOut(_Schema):
    passenger_index: int | None
    seat: str

    @classmethod
    def from_domain(cls, seat: SeatAssignment) -> SeatOut:
        return cls(passenger_index=seat.passenger_index, seat=seat.seat)


class SegmentStatusOut(_Schema):
    code: str
    category: SegmentStatusCategory
    description: str | None


class FlightSegmentOut(_Schema):
    index: int
    carrier: str
    flight_number: str
    booking_class: str
    origin: str
    destination: str
    departure_local: datetime = Field(description="Local time at the origin airport.")
    arrival_local: datetime = Field(description="Local time at the destination airport.")
    status: SegmentStatusOut
    passenger_count: int
    airline: AirlineOut | None
    operated_by: str | None = Field(
        description="Operating airline of a codeshare flight, as the GDS prints it."
    )
    origin_airport: AirportOut | None
    destination_airport: AirportOut | None
    departure_at: datetime | None = Field(
        description="Departure with UTC offset; null if the origin airport is unknown."
    )
    arrival_at: datetime | None = Field(
        description="Arrival with UTC offset; null if the destination airport is unknown."
    )
    duration_minutes: int | None
    distance: DistanceOut | None = Field(
        description="Shortest distance between the airports (WGS84 ellipsoid)."
    )
    seats: list[SeatOut]

    @classmethod
    def from_domain(
        cls, enriched: EnrichedSegment, seats: list[SeatAssignment]
    ) -> FlightSegmentOut:
        segment = enriched.segment
        return cls(
            index=segment.index,
            carrier=segment.carrier,
            flight_number=segment.flight_number,
            booking_class=segment.booking_class,
            origin=segment.origin,
            destination=segment.destination,
            departure_local=segment.departure,
            arrival_local=segment.arrival,
            status=SegmentStatusOut(
                code=segment.status.code,
                category=segment.status.category,
                description=segment.status.description,
            ),
            passenger_count=segment.passenger_count,
            airline=AirlineOut.from_domain(enriched.airline),
            operated_by=segment.operated_by,
            origin_airport=AirportOut.from_domain(enriched.origin),
            destination_airport=AirportOut.from_domain(enriched.destination),
            departure_at=enriched.departure_at,
            arrival_at=enriched.arrival_at,
            duration_minutes=_minutes(enriched.duration),
            distance=DistanceOut.from_km(enriched.distance_km),
            seats=[SeatOut.from_domain(seat) for seat in seats],
        )


class ConnectionOut(_Schema):
    airport: str
    duration_minutes: int | None

    @classmethod
    def from_domain(cls, connection: Connection) -> ConnectionOut:
        return cls(airport=connection.airport, duration_minutes=_minutes(connection.duration))


class JourneyOut(_Schema):
    segment_indexes: list[int]
    origin: str
    destination: str
    departure_at: datetime | None
    arrival_at: datetime | None
    duration_minutes: int | None
    distance: DistanceOut | None
    connections: list[ConnectionOut]

    @classmethod
    def from_domain(cls, journey: Journey) -> JourneyOut:
        return cls(
            segment_indexes=[s.segment.index for s in journey.segments],
            origin=journey.origin,
            destination=journey.destination,
            departure_at=journey.departure_at,
            arrival_at=journey.arrival_at,
            duration_minutes=_minutes(journey.duration),
            distance=DistanceOut.from_km(journey.distance_km),
            connections=[ConnectionOut.from_domain(c) for c in journey.connections],
        )


class TicketOut(_Schema):
    number: str
    passenger_index: int | None
    issuing_airline: str | None
    issue_date: date | None
    electronic: bool
    infant: bool = Field(description="Ticket issued for the lap infant of `passenger_index`.")

    @classmethod
    def from_domain(cls, ticket: Ticket) -> TicketOut:
        return cls(
            number=ticket.number,
            passenger_index=ticket.passenger_index,
            issuing_airline=ticket.issuing_airline,
            issue_date=ticket.issue_date,
            electronic=ticket.electronic,
            infant=ticket.infant,
        )


class ContactOut(_Schema):
    kind: ContactKind
    text: str = Field(description="Verbatim contact element, including any GDS prefix.")

    @classmethod
    def from_domain(cls, contact: Contact) -> ContactOut:
        return cls(kind=contact.kind, text=contact.text)


class WarningOut(_Schema):
    line_number: int
    message: str

    @classmethod
    def from_domain(cls, warning: ParseWarning) -> WarningOut:
        return cls(line_number=warning.line_number, message=warning.message)


class ConvertResponse(_Schema):
    gds: GdsFormat
    record_locator: str | None
    passengers: list[PassengerOut]
    segments: list[FlightSegmentOut]
    journeys: list[JourneyOut] = Field(
        description="Segments grouped into trips; a break over 24h starts a new journey. "
        "Cancelled segments are excluded."
    )
    tickets: list[TicketOut]
    contacts: list[ContactOut]
    warnings: list[WarningOut]

    @classmethod
    def from_domain(cls, itinerary: Itinerary) -> ConvertResponse:
        pnr = itinerary.pnr
        seats_by_segment: dict[int, list[SeatAssignment]] = {}
        for seat in pnr.seats:
            seats_by_segment.setdefault(seat.segment_index, []).append(seat)
        return cls(
            gds=pnr.gds,
            record_locator=pnr.record_locator,
            passengers=[PassengerOut.from_domain(p) for p in pnr.passengers],
            segments=[
                FlightSegmentOut.from_domain(s, seats_by_segment.get(s.segment.index, []))
                for s in itinerary.segments
            ],
            journeys=[JourneyOut.from_domain(j) for j in itinerary.journeys],
            tickets=[TicketOut.from_domain(t) for t in pnr.tickets],
            contacts=[ContactOut.from_domain(c) for c in pnr.contacts],
            warnings=[WarningOut.from_domain(w) for w in pnr.warnings],
        )
