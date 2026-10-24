from __future__ import annotations

import pytest

from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.apollo import ApolloParser
from pnr_convertor.parsing.base import ParseContext, PnrParser
from pnr_convertor.parsing.galileo import GalileoParser
from pnr_convertor.parsing.sabre import SabreParser
from pnr_convertor.parsing.worldspan import WorldspanParser
from tests.conftest import REFERENCE_DATE

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)

SEGMENTS: dict[str, tuple[PnrParser, str, str]] = {
    "amadeus": (
        AmadeusParser(),
        "  1  KL1371 Y 05DEC 5 OTPAMS HK1  0715 0905  05DEC  E  KL/ABC123",
        "  2  KL 643 Y 05DEC 5 AMSJFK HK1  1015 1225  05DEC  E  KL/ABC123",
    ),
    "sabre": (
        SabreParser(),
        " 1 KL1371Y 5DEC F OTPAMS HK1 715A 905A /DCKL*ABC123 /E",
        " 2 KL 643Y 5DEC F AMSJFK HK1 1015A 1225P /DCKL*ABC123 /E",
    ),
    "galileo": (
        GalileoParser(),
        " 1. KL 1371 Y 05DEC OTPAMS HK1  0715   0905  O*        E FR",
        " 2. KL  643 Y 05DEC AMSJFK HK1  1015   1225  O*        E FR",
    ),
    "worldspan": (
        WorldspanParser(),
        " 1 KL1371Y 05DEC FR OTPAMS HK1  0715  0905 /O $ E",
        " 2 KL 643Y 05DEC FR AMSJFK HK1  1015  1225 /X $ E",
    ),
    "apollo": (
        ApolloParser(),
        " 1 KL1371Y 05DEC OTPAMS HK1   715A  905A *        FR   E  1",
        " 2 KL 643Y 05DEC AMSJFK HK1  1015A 1225P *        FR   E  1",
    ),
}


@pytest.mark.parametrize("gds", SEGMENTS)
def test_operated_by_line_belongs_to_the_segment_above(gds: str) -> None:
    parser, first, second = SEGMENTS[gds]
    text = f"{first}\n     OPERATED BY AIR ROMANIA SA\n{second}"
    pnr = parser.parse(text, CONTEXT)

    assert [s.index for s in pnr.segments] == [1, 2]
    assert [s.operated_by for s in pnr.segments] == ["AIR ROMANIA SA", None]


@pytest.mark.parametrize("gds", SEGMENTS)
def test_operated_by_before_any_segment_is_ignored(gds: str) -> None:
    parser, first, _ = SEGMENTS[gds]
    pnr = parser.parse(f"OPERATED BY AIR ROMANIA SA\n{first}", CONTEXT)
    assert pnr.segments[0].operated_by is None
