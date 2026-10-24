from __future__ import annotations

import pytest

from pnr_convertor.domain.errors import UnsupportedFormatError
from pnr_convertor.domain.models import GdsFormat
from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.registry import ParserRegistry
from tests.conftest import read_fixture


@pytest.fixture
def registry() -> ParserRegistry:
    return ParserRegistry([AmadeusParser()])


def test_auto_detects_amadeus(registry: ParserRegistry) -> None:
    parser = registry.resolve(read_fixture("amadeus", "basic_return"))
    assert parser.gds is GdsFormat.AMADEUS


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
