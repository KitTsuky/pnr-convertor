from __future__ import annotations

from zoneinfo import ZoneInfo

import pytest

from pnr_convertor.domain.reference import Airline, Airport
from pnr_convertor.infrastructure.reference_data import (
    BundledAirlineRepository,
    BundledAirportRepository,
)


@pytest.fixture(scope="module")
def airports() -> BundledAirportRepository:
    return BundledAirportRepository()


@pytest.fixture(scope="module")
def airlines() -> BundledAirlineRepository:
    return BundledAirlineRepository()


def test_known_airport(airports: BundledAirportRepository) -> None:
    assert airports.get("OTP") == Airport(
        iata="OTP",
        name="Henri Coanda International Airport",
        city="Bucharest",
        country="RO",
        timezone="Europe/Bucharest",
        latitude=44.5722,
        longitude=26.1022,
    )


def test_airport_timezone_is_valid_iana_zone(airports: BundledAirportRepository) -> None:
    airport = airports.get("JFK")
    assert airport is not None
    assert ZoneInfo(airport.timezone).key == "America/New_York"


def test_unknown_airport(airports: BundledAirportRepository) -> None:
    assert airports.get("ZZZ") is None


@pytest.mark.parametrize(
    ("code", "name"),
    [("RO", "Tarom"), ("BA", "British Airways"), ("LH", "Lufthansa"), ("W6", "Wizz Air")],
)
def test_known_airline(airlines: BundledAirlineRepository, code: str, name: str) -> None:
    assert airlines.get(code) == Airline(iata=code, name=name)


def test_unknown_airline(airlines: BundledAirlineRepository) -> None:
    assert airlines.get("??") is None
