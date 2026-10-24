"""Builders and in-memory fakes shared by tests."""

from __future__ import annotations

from datetime import datetime

from pnr_convertor.domain.models import FlightSegment, SegmentStatus
from pnr_convertor.domain.reference import Airline, Airport

AIRPORTS = {
    airport.iata: airport
    for airport in [
        Airport("OTP", "Henri Coanda International Airport", "Bucharest", "RO", "Europe/Bucharest"),
        Airport("CDG", "Charles de Gaulle International Airport", "Paris", "FR", "Europe/Paris"),
        Airport("LHR", "London Heathrow Airport", "London", "GB", "Europe/London"),
        Airport(
            "JFK", "John F Kennedy International Airport", "New York", "US", "America/New_York"
        ),
        Airport("DXB", "Dubai International Airport", "Dubai", "AE", "Asia/Dubai"),
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
