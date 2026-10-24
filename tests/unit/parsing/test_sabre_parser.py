from __future__ import annotations

from datetime import datetime

import pytest

from pnr_convertor.domain.models import SegmentStatusCategory
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.sabre import SabreParser
from tests.conftest import REFERENCE_DATE, read_fixture

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)


@pytest.fixture
def parser() -> SabreParser:
    return SabreParser()


class TestDetect:
    def test_segment_line_is_recognized(self, parser: SabreParser) -> None:
        assert parser.detect(read_fixture("sabre", "next_day_arrival")) == 0.9

    def test_amadeus_text_is_not_recognized(self, parser: SabreParser) -> None:
        assert parser.detect(read_fixture("amadeus", "basic_return")) == 0.0


class TestSegments:
    def test_parses_all_fields(self, parser: SabreParser) -> None:
        line = " 1 AI 174J 14JUN J SFODEL SS2  1000A  345P  15JUN S /DCAI /E"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert segment.index == 1
        assert (segment.carrier, segment.flight_number, segment.booking_class) == ("AI", "174", "J")
        assert (segment.origin, segment.destination) == ("SFO", "DEL")
        assert segment.departure == datetime(2025, 6, 14, 10, 0)
        assert segment.arrival == datetime(2025, 6, 15, 15, 45)
        assert segment.status.category is SegmentStatusCategory.CONFIRMED
        assert segment.passenger_count == 2

    def test_four_digit_flight_glued_to_carrier_and_asterisk_before_status(
        self, parser: SabreParser
    ) -> None:
        line = " 2 AA7386D 13JUL S DFWMEL*SS2   825P  500A  15JUL T /DCAA /E"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert (segment.carrier, segment.flight_number, segment.booking_class) == (
            "AA",
            "7386",
            "D",
        )
        assert segment.status.code == "SS"
        assert segment.arrival == datetime(2025, 7, 15, 5, 0)

    def test_weekday_letters_resolve_chained_years(self, parser: SabreParser) -> None:
        pnr = parser.parse(read_fixture("sabre", "multi_city_connections"), CONTEXT)
        assert [s.departure.date().isoformat() for s in pnr.segments] == [
            "2025-07-13",
            "2025-07-13",
            "2025-10-25",
            "2025-10-25",
            "2025-10-25",
        ]

    def test_ignores_fare_quote_and_verify_lines(self, parser: SabreParser) -> None:
        pnr = parser.parse(read_fixture("sabre", "verify_itinerary_and_display"), CONTEXT)
        assert [s.index for s in pnr.segments] == [1, 2]
        assert pnr.warnings == ()

    def test_invalid_segment_is_skipped_with_warning(self, parser: SabreParser) -> None:
        text = (
            " 1 AA 142J 31APR M JFKLHR SS2   945A  940P\n 2 AA 101O 05JUN Q LHRJFK SS2   945A 1229P"
        )
        pnr = parser.parse(text, CONTEXT)

        assert [s.index for s in pnr.segments] == [2]
        assert pnr.warnings[0].line_number == 1

    def test_itinerary_display_has_no_passengers_or_locator(self, parser: SabreParser) -> None:
        pnr = parser.parse(read_fixture("sabre", "next_day_arrival"), CONTEXT)
        assert pnr.passengers == ()
        assert pnr.record_locator is None
