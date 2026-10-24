from __future__ import annotations

from datetime import date

import pytest

from pnr_convertor.application.convert_pnr import ConvertPnr, ConvertPnrCommand
from pnr_convertor.bootstrap import build_parser_registry
from pnr_convertor.domain.errors import PnrParseError
from tests.conftest import FixedClock, read_fixture


@pytest.fixture
def use_case() -> ConvertPnr:
    return ConvertPnr(build_parser_registry(), FixedClock())


def test_normalizes_input_before_parsing(use_case: ConvertPnr) -> None:
    text = read_fixture("amadeus", "basic_return").lower().replace("\n", "\r\n")
    pnr = use_case.execute(ConvertPnrCommand(text=text))
    assert pnr.record_locator == "ZX7K2P"
    assert len(pnr.segments) == 2


def test_explicit_reference_date_overrides_clock(use_case: ConvertPnr) -> None:
    text = "  1  RO 391 Y 15MAR OTPCDG HK1  0710 0920"
    pnr = use_case.execute(ConvertPnrCommand(text=text, reference_date=date(2030, 1, 1)))
    assert pnr.segments[0].departure.year == 2030


def test_pnr_without_segments_is_rejected(use_case: ConvertPnr) -> None:
    text = "RP/BUHRO08AA/BUHRO08AA            AA/SU  10JAN26/0915Z   ZX7K2P\n  1.DOE/JANE"
    with pytest.raises(PnrParseError, match="No flight segments"):
        use_case.execute(ConvertPnrCommand(text=text))
