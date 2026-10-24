from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from pnr_convertor.application.enrich_itinerary import ItineraryEnricher
from pnr_convertor.domain.itinerary import Itinerary
from pnr_convertor.domain.models import (
    Contact,
    ContactKind,
    FlightSegment,
    GdsFormat,
    Infant,
    ParsedPnr,
    Passenger,
    SeatAssignment,
    Ticket,
)
from pnr_convertor.rendering.view import build_view
from tests.factories import InMemoryAirlineRepository, InMemoryAirportRepository, make_segment

ENRICHER = ItineraryEnricher(InMemoryAirportRepository(), InMemoryAirlineRepository())
JANE = Passenger(1, "DOE", "JANE", "MRS")


def _itinerary(
    *segments: FlightSegment,
    passengers: tuple[Passenger, ...] = (JANE,),
    seats: tuple[SeatAssignment, ...] = (),
    tickets: tuple[Ticket, ...] = (),
    contacts: tuple[Contact, ...] = (),
) -> Itinerary:
    return ENRICHER.enrich(
        ParsedPnr(
            GdsFormat.AMADEUS,
            "ABC123",
            passengers,
            segments,
            seats=seats,
            tickets=tickets,
            contacts=contacts,
        )
    )


def test_journey_with_a_connection() -> None:
    view = build_view(
        _itinerary(
            make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=1),
            make_segment(
                "CDG", "JFK", "2026-03-15T11:00", "2026-03-15T13:30", index=2, carrier="AF"
            ),
        )
    )

    (journey,) = view.journeys
    assert journey.title == "Bucharest (OTP) to New York (JFK)"
    assert journey.date == "Sun 15 Mar 2026"
    assert journey.stops == "1 connection (CDG)"
    assert journey.duration == "12h 20m"
    assert journey.connections == ("Connection in Paris (CDG): 1h 40m",)
    first, second = journey.flights
    assert (first.flight, first.airline, first.status) == ("RO 100", "Tarom", "Confirmed")
    assert first.departure.time == "Sun 15 Mar 2026 07:10"
    assert first.departure.airport == "Henri Coanda Intl"
    assert first.duration == "3h 10m"
    assert second.airline == "Air France"


def test_unknown_airport_and_airline_fall_back_to_codes() -> None:
    view = build_view(
        _itinerary(make_segment("ZZZ", "OTP", "2026-03-15T07:10", "2026-03-15T07:50", carrier="Q9"))
    )

    (flight,) = view.journeys[0].flights
    assert (flight.airline, flight.departure.place, flight.departure.airport) == ("Q9", "ZZZ", None)
    assert (flight.duration, flight.distance) == (None, None)


def test_short_flight_duration_has_no_hours() -> None:
    view = build_view(
        _itinerary(make_segment("CDG", "LHR", "2026-03-15T07:10", "2026-03-15T07:25"))
    )
    assert view.journeys[0].flights[0].duration == "1h 15m"
    view = build_view(
        _itinerary(make_segment("LHR", "CDG", "2026-03-15T07:10", "2026-03-15T08:50"))
    )
    assert view.journeys[0].flights[0].duration == "40m"


def test_cancelled_segments_are_listed_apart() -> None:
    view = build_view(
        _itinerary(
            make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=1),
            make_segment(
                "CDG", "OTP", "2026-03-20T10:00", "2026-03-20T14:00", index=2, status="HX"
            ),
        )
    )

    assert [len(j.flights) for j in view.journeys] == [1]
    (cancelled,) = view.cancelled
    assert cancelled.status == "Cancelled"


@pytest.mark.parametrize(("code", "label"), [("GK", "Passive segment"), ("ZZ", "ZZ")])
def test_status_without_a_category(code: str, label: str) -> None:
    view = build_view(
        _itinerary(make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", status=code))
    )
    assert view.journeys[0].flights[0].status == label


def test_passengers_tickets_seats_and_contacts() -> None:
    mother = replace(JANE, infant=Infant("DOE", "BABY", date(2025, 3, 15)))
    child = Passenger(2, "DOE", "TOM", None, "CHD")
    view = build_view(
        _itinerary(
            make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=3),
            passengers=(mother, child),
            seats=(SeatAssignment(3, 1, "12A"), SeatAssignment(3, None, "12B")),
            tickets=(
                Ticket("281-1234567890", 1, "RO", date(2026, 1, 10), electronic=True),
                Ticket("281-1234567891", 1, "RO", None, electronic=True, infant=True),
                Ticket("281-1234567892", None, None, None, electronic=True),
            ),
            contacts=(Contact(ContactKind.EMAIL, "DOE@EXAMPLE.COM"),),
        )
    )

    assert [(p.name, p.type, p.infant) for p in view.passengers] == [
        ("DOE/JANE MRS", "Adult", "DOE/BABY, born 15 Mar 2025"),
        ("DOE/TOM", "Child", None),
    ]
    assert view.journeys[0].flights[0].seats == ("12A DOE/JANE MRS", "12B")
    assert [(t.passenger, t.issued) for t in view.tickets] == [
        ("DOE/JANE MRS", "10 Jan 2026"),
        ("infant of DOE/JANE MRS", None),
        (None, None),
    ]
    assert view.contacts == ("Email: DOE@EXAMPLE.COM",)


def test_unlisted_passenger_type_is_shown_as_is() -> None:
    view = build_view(_itinerary(passengers=(replace(JANE, type_code="STU"),)))
    assert view.passengers[0].type == "STU"


def test_journey_stops_wording() -> None:
    direct = build_view(
        _itinerary(make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20"))
    )
    two = build_view(
        _itinerary(
            make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=1),
            make_segment("CDG", "LHR", "2026-03-15T11:00", "2026-03-15T11:20", index=2),
            make_segment("LHR", "JFK", "2026-03-15T13:00", "2026-03-15T16:00", index=3),
        )
    )
    assert direct.journeys[0].stops == "Direct"
    assert two.journeys[0].stops == "2 connections (CDG, LHR)"
