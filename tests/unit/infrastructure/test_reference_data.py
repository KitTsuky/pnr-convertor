from __future__ import annotations

from zoneinfo import ZoneInfo

import pytest

from pnr_convertor.domain.reference import Airline, Airport
from pnr_convertor.infrastructure.reference_data import (
    BundledAirlineLogoRepository,
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


def test_city_override_drops_the_district(airports: BundledAirportRepository) -> None:
    airport = airports.get("IST")
    assert airport is not None
    assert airport.city == "Istanbul"


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


def test_logos_are_read_only_for_listed_codes() -> None:
    logos = BundledAirlineLogoRepository()

    assert "TK" in logos.codes
    assert (logos.get("TK") or b"").startswith(b"\x89PNG")
    assert logos.get("ZZ") is None
    assert logos.get("../airlines") is None


def test_airlines_know_whether_they_have_a_logo() -> None:
    airlines = BundledAirlineRepository(logo_codes={"RO"})

    assert airlines.get("RO") == Airline(iata="RO", name="Tarom", has_logo=True)
    assert airlines.get("BA") == Airline(iata="BA", name="British Airways")
