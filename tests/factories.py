"""Builders and in-memory fakes shared by tests."""

from __future__ import annotations

from datetime import datetime

from pnr_convertor.domain.models import FlightSegment, SegmentStatus
from pnr_convertor.domain.reference import Airline, Airport

AIRPORTS = {
    airport.iata: airport
    for airport in [
        Airport(
            "OTP", "Henri Coanda Intl", "Bucharest", "RO", "Europe/Bucharest", 44.5722, 26.1022
        ),
        Airport("CDG", "Charles de Gaulle Intl", "Paris", "FR", "Europe/Paris", 49.0128, 2.55),
        Airport("LHR", "London Heathrow", "London", "GB", "Europe/London", 51.4706, -0.46194),
        Airport(
            "JFK",
            "John F Kennedy Intl",
            "New York",
            "US",
            "America/New_York",
            40.639928,
            -73.778692,
        ),
        Airport("DXB", "Dubai Intl", "Dubai", "AE", "Asia/Dubai", 25.2528, 55.3644),
    ]
}

AIRLINES = {
    airline.iata: airline
    for airline in [
        Airline("RO", "Tarom"),
        Airline("AF", "Air France"),
        Airline("BA", "British Airways"),
    ]
}


class InMemoryAirportRepository:
    def get(self, iata: str) -> Airport | None:
        return AIRPORTS.get(iata)


class InMemoryAirlineRepository:
    def get(self, iata: str) -> Airline | None:
        return AIRLINES.get(iata)


def make_segment(
    origin: str,
    destination: str,
    departure: str,
    arrival: str,
    *,
    index: int = 1,
    carrier: str = "RO",
    status: str = "HK",
) -> FlightSegment:
    return FlightSegment(
        index=index,
        carrier=carrier,
        flight_number="100",
        booking_class="Y",
        origin=origin,
        destination=destination,
        departure=datetime.fromisoformat(departure),
        arrival=datetime.fromisoformat(arrival),
        status=SegmentStatus(status),
        passenger_count=1,
    )
