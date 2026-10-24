from __future__ import annotations

import pytest

from pnr_convertor.domain.errors import UnsupportedFormatError
from pnr_convertor.domain.models import GdsFormat
from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.apollo import ApolloParser
from pnr_convertor.parsing.galileo import GalileoParser
from pnr_convertor.parsing.registry import ParserRegistry
from pnr_convertor.parsing.sabre import SabreParser
from pnr_convertor.parsing.worldspan import WorldspanParser
from tests.conftest import read_fixture


@pytest.fixture
def registry() -> ParserRegistry:
    return ParserRegistry(
        [AmadeusParser(), SabreParser(), GalileoParser(), WorldspanParser(), ApolloParser()]
    )


def test_auto_detects_amadeus(registry: ParserRegistry) -> None:
    parser = registry.resolve(read_fixture("amadeus", "basic_return"))
    assert parser.gds is GdsFormat.AMADEUS


def test_auto_detects_sabre(registry: ParserRegistry) -> None:
    parser = registry.resolve(read_fixture("sabre", "round_trip_with_fare_quote"))
    assert parser.gds is GdsFormat.SABRE


def test_auto_detects_galileo(registry: ParserRegistry) -> None:
    parser = registry.resolve(read_fixture("galileo", "booking_file_connections"))
    assert parser.gds is GdsFormat.GALILEO


def test_auto_detects_worldspan(registry: ParserRegistry) -> None:
    parser = registry.resolve(read_fixture("worldspan", "ticketed_overnight_connections"))
    assert parser.gds is GdsFormat.WORLDSPAN


@pytest.mark.parametrize("name", ["overnight_codeshare_connection", "family_child_infant_waitlist"])
def test_apollo_is_not_mistaken_for_galileo(registry: ParserRegistry, name: str) -> None:
    assert registry.resolve(read_fixture("apollo", name)).gds is GdsFormat.APOLLO


@pytest.mark.parametrize(
    ("gds", "name"),
    [
        ("galileo", "booking_file_connections"),
        ("galileo", "statuses_children_and_infant"),
        ("galileo", "phones_and_ticketing_field"),
    ],
)
def test_galileo_is_not_mistaken_for_apollo(registry: ParserRegistry, gds: str, name: str) -> None:
    assert registry.resolve(read_fixture(gds, name)).gds is GdsFormat.GALILEO


def test_explicit_format_skips_detection(registry: ParserRegistry) -> None:
    assert registry.resolve("anything", GdsFormat.AMADEUS).gds is GdsFormat.AMADEUS


def test_unrecognized_text_raises(registry: ParserRegistry) -> None:
    with pytest.raises(UnsupportedFormatError, match="Could not recognize"):
        registry.resolve("not a pnr")


def test_explicit_format_without_parser_raises() -> None:
    with pytest.raises(UnsupportedFormatError, match="No parser available"):
        ParserRegistry([]).resolve("anything", GdsFormat.AMADEUS)


def test_duplicate_registration_is_rejected() -> None:
    with pytest.raises(ValueError, match="Duplicate parser"):
        ParserRegistry([AmadeusParser(), AmadeusParser()])
