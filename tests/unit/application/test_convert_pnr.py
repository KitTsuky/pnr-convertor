from __future__ import annotations

from datetime import date

import pytest

from pnr_convertor.application.convert_pnr import ConvertPnr, ConvertPnrCommand
from pnr_convertor.bootstrap import Container
from pnr_convertor.domain.errors import PnrParseError
from tests.conftest import read_fixture


@pytest.fixture
def use_case(container: Container) -> ConvertPnr:
    return container.convert_pnr


def test_normalizes_input_before_parsing(use_case: ConvertPnr) -> None:
    text = read_fixture("amadeus", "basic_return").lower().replace("\n", "\r\n")
    itinerary = use_case.execute(ConvertPnrCommand(text=text))
    assert itinerary.pnr.record_locator == "ZX7K2P"
    assert len(itinerary.segments) == 2


def test_explicit_reference_date_overrides_clock(use_case: ConvertPnr) -> None:
    text = "  1  RO 391 Y 15MAR OTPCDG HK1  0710 0920"
    itinerary = use_case.execute(ConvertPnrCommand(text=text, reference_date=date(2030, 1, 1)))
    assert itinerary.pnr.segments[0].departure.year == 2030


def test_pnr_without_segments_is_rejected(use_case: ConvertPnr) -> None:
    text = "RP/BUHRO08AA/BUHRO08AA            AA/SU  10JAN26/0915Z   ZX7K2P\n  1.DOE/JANE"
    with pytest.raises(PnrParseError, match="No flight segments"):
        use_case.execute(ConvertPnrCommand(text=text))


def test_returns_enriched_itinerary(use_case: ConvertPnr) -> None:
    itinerary = use_case.execute(ConvertPnrCommand(text=read_fixture("amadeus", "basic_return")))
    assert [(j.origin, j.destination) for j in itinerary.journeys] == [
        ("OTP", "CDG"),
        ("CDG", "OTP"),
    ]
    assert itinerary.segments[0].airline is not None
