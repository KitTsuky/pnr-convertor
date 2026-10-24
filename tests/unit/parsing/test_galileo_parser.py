from __future__ import annotations

from datetime import date, datetime

import pytest

from pnr_convertor.domain.models import Passenger, SegmentStatusCategory
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.galileo import GalileoParser
from tests.conftest import REFERENCE_DATE, read_fixture

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)


@pytest.fixture
def parser() -> GalileoParser:
    return GalileoParser()


class TestDetect:
    def test_header_gives_full_confidence(self, parser: GalileoParser) -> None:
        assert parser.detect(read_fixture("galileo", "booking_file_connections")) == 1.0

    def test_segment_without_header(self, parser: GalileoParser) -> None:
        line = " 1 . CX  640 N  20JUN KTMHKG HS1  2300  #0600  O         E SA/SU 1"
        assert parser.detect(line) == 0.8

    @pytest.mark.parametrize(
        ("gds", "name"), [("amadeus", "basic_return"), ("sabre", "next_day_arrival")]
    )
    def test_other_formats_are_not_recognized(
        self, parser: GalileoParser, gds: str, name: str
    ) -> None:
        assert parser.detect(read_fixture(gds, name)) == 0.0


class TestSegments:
    def test_parses_all_fields(self, parser: GalileoParser) -> None:
        line = "   3 . KL  644 Y  12DEC JFKAMS HK2  1830  #0745  O*    E FR/SA"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert segment.index == 3
        assert (segment.carrier, segment.flight_number, segment.booking_class) == ("KL", "644", "Y")
        assert (segment.origin, segment.destination) == ("JFK", "AMS")
        assert segment.departure == datetime(2025, 12, 12, 18, 30)
        assert segment.arrival == datetime(2025, 12, 13, 7, 45)
        assert segment.status.category is SegmentStatusCategory.CONFIRMED
        assert segment.passenger_count == 2

    @pytest.mark.parametrize(
        ("line", "arrival"),
        [
            pytest.param(
                " 1 . QF    2 Y  10JAN LHRSYD HS2  2105  *0625  O*  E SA/MO",
                date(2026, 1, 12),
                id="two-days",
            ),
            pytest.param(
                " 1 . NZ    1 Y  12JAN AKLLAX HK1  1930  -1030  O   E MO/SU",
                date(2026, 1, 11),
                id="previous-day",
            ),
            pytest.param(
                " 1. BA 113 Y 13JAN JFKLHR HK1  2100 0830 +1 E", date(2026, 1, 14), id="plus-offset"
            ),
            pytest.param(
                " 1. BA 112 Y 13JAN LHRJFK HK1  0825 1130  O E", date(2026, 1, 13), id="same-day"
            ),
        ],
    )
    def test_arrival_day_markers(self, parser: GalileoParser, line: str, arrival: date) -> None:
        (segment,) = parser.parse(line, CONTEXT).segments
        assert segment.arrival.date() == arrival

    def test_weekday_identifies_the_year(self, parser: GalileoParser) -> None:
        line = "   1 . KL  888 M  10MAY HKGAMS HK1  1220   1835  O*    E SU"
        (segment,) = parser.parse(line, ParseContext(reference_date=date(2026, 10, 24))).segments
        assert segment.departure.date() == date(2026, 5, 10)

    def test_status_with_space_and_holding_sold(self, parser: GalileoParser) -> None:
        (segment,) = parser.parse(
            "  1.   BA   107   F 25OCT  LHRDXB  HS 1  1255  2305  O", CONTEXT
        ).segments
        assert (segment.status.code, segment.passenger_count) == ("HS", 1)
        assert segment.status.description == "Holding sold"

    def test_invalid_segment_is_skipped_with_warning(self, parser: GalileoParser) -> None:
        text = (
            " 1 . KL  644 Y  31APR JFKAMS HK2  1830  #0745  O*  E\n"
            " 2 . KL  645 Y  02MAY AMSJFK HK2  1015  1225  O*  E"
        )
        pnr = parser.parse(text, CONTEXT)
        assert [s.index for s in pnr.segments] == [2]
        assert pnr.warnings[0].line_number == 1


class TestBookingFile:
    def test_record_locator_from_header(self, parser: GalileoParser) -> None:
        pnr = parser.parse(read_fixture("galileo", "booking_file_connections"), CONTEXT)
        assert pnr.record_locator == "K7PL2Q"

    def test_names_with_glued_titles(self, parser: GalileoParser) -> None:
        pnr = parser.parse("  1.1POPESCU/ANDREIMR 2.1POPESCU/MARIAMRS", CONTEXT)
        assert pnr.passengers == (
            Passenger(1, "POPESCU", "ANDREI", "MR"),
            Passenger(2, "POPESCU", "MARIA", "MRS"),
        )

    @pytest.mark.parametrize(
        ("item", "type_code"),
        [
            ("*ADT", "ADT"),
            ("*CHD", "CHD"),
            ("*C05", "CHD"),
            ("*ITX", "ITX"),
            ("*P-108", "ADT"),
            ("", "ADT"),
        ],
    )
    def test_passenger_type_suffix(self, parser: GalileoParser, item: str, type_code: str) -> None:
        (passenger,) = parser.parse(f"  1.1DOE/ANAMS{item}", CONTEXT).passengers
        assert passenger.type_code == type_code

    def test_infant_item(self, parser: GalileoParser) -> None:
        (infant,) = parser.parse("  3.I/1IONESCU/SARAMISS*14JAN25", CONTEXT).passengers
        assert infant == Passenger(3, "IONESCU", "SARA", "MISS", "INF", date(2025, 1, 14))

    def test_vendor_locator_banner_is_ignored(self, parser: GalileoParser) -> None:
        pnr = parser.parse(read_fixture("galileo", "booking_file_connections"), CONTEXT)
        assert pnr.warnings == ()
        assert len(pnr.segments) == 4
