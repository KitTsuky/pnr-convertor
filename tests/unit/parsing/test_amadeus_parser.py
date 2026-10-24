from __future__ import annotations

from datetime import datetime

import pytest

from pnr_convertor.domain.models import Passenger, SegmentStatusCategory
from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.base import ParseContext
from tests.conftest import REFERENCE_DATE, read_fixture

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)


@pytest.fixture
def parser() -> AmadeusParser:
    return AmadeusParser()


class TestDetect:
    def test_header_gives_full_confidence(self, parser: AmadeusParser) -> None:
        assert parser.detect(read_fixture("amadeus", "basic_return")) == 1.0

    def test_segment_without_header_gives_partial_confidence(self, parser: AmadeusParser) -> None:
        text = "  1  RO 391 Y 15MAR 7 OTPCDG HK1  0710 0920"
        assert 0.5 <= parser.detect(text) < 1.0

    def test_unrelated_text_gives_zero(self, parser: AmadeusParser) -> None:
        assert parser.detect("hello, this is not a PNR") == 0.0


class TestSegments:
    def test_parses_all_fields(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  3  RO 391 Y 15MAR 7 OTPCDG HK2  0710 0920   15MAR  E", CONTEXT)

        (segment,) = pnr.segments
        assert segment.index == 3
        assert segment.carrier == "RO"
        assert segment.flight_number == "391"
        assert segment.booking_class == "Y"
        assert segment.origin == "OTP"
        assert segment.destination == "CDG"
        assert segment.departure == datetime(2026, 3, 15, 7, 10)
        assert segment.arrival == datetime(2026, 3, 15, 9, 20)
        assert segment.status.code == "HK"
        assert segment.status.category is SegmentStatusCategory.CONFIRMED
        assert segment.passenger_count == 2

    @pytest.mark.parametrize(
        "line",
        [
            pytest.param(
                "  1  AF1088 Y 22MAR 7 CDGOTP HK1  1945 2350", id="flight-glued-to-carrier"
            ),
            pytest.param("  1  AF 1088Y 22MAR CDGOTP HK1  1945 2350", id="class-glued-no-weekday"),
            pytest.param("1 AF 1088 Y 22MAR 7 CDGOTP HK1 1945 2350", id="single-spaced"),
        ],
    )
    def test_tolerates_spacing_variants(self, parser: AmadeusParser, line: str) -> None:
        (segment,) = parser.parse(line, CONTEXT).segments
        assert (segment.carrier, segment.flight_number, segment.booking_class) == (
            "AF",
            "1088",
            "Y",
        )

    def test_day_offset_moves_arrival_to_next_day(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1  EK 202 J 30DEC 2 JFKDXB HK1  2300 1930+1", CONTEXT)
        (segment,) = pnr.segments
        assert segment.departure == datetime(2025, 12, 30, 23, 0)
        assert segment.arrival == datetime(2025, 12, 31, 19, 30)

    def test_later_segments_roll_over_into_next_year(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "overnight_year_rollover"), CONTEXT)
        assert [s.departure.date().isoformat() for s in pnr.segments] == [
            "2025-12-28",
            "2025-12-30",
            "2026-01-03",
        ]

    @pytest.mark.parametrize(
        ("code", "category"),
        [
            ("HL", SegmentStatusCategory.WAITLISTED),
            ("HN", SegmentStatusCategory.REQUESTED),
            ("HX", SegmentStatusCategory.CANCELLED),
            ("ZZ", SegmentStatusCategory.UNKNOWN),
        ],
    )
    def test_status_categories(
        self, parser: AmadeusParser, code: str, category: SegmentStatusCategory
    ) -> None:
        (segment,) = parser.parse(
            f"  1  RO 391 Y 15MAR OTPCDG {code}1  0710 0920", CONTEXT
        ).segments
        assert segment.status.category is category

    def test_invalid_segment_is_skipped_with_warning(self, parser: AmadeusParser) -> None:
        text = (
            "  1  RO 391 Y 31APR OTPCDG HK1  0710 0920\n  2  RO 392 Y 15MAY OTPCDG HK1  0710 0920"
        )
        pnr = parser.parse(text, CONTEXT)

        assert [s.index for s in pnr.segments] == [2]
        (warning,) = pnr.warnings
        assert warning.line_number == 1
        assert "Skipped air segment" in warning.message

    def test_non_segment_elements_are_ignored(self, parser: AmadeusParser) -> None:
        text = "  5 AP BUH 021 555 0100\n  6 TK OK10JAN/BUHRO08AA\n  7 OSI YY 1234"
        assert parser.parse(text, CONTEXT).segments == ()


class TestPassengersAndHeader:
    def test_parses_multiple_passengers_on_one_line(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1.POPESCU/ANDREI MR   2.POPESCU/MARIA ELENA MRS", CONTEXT)
        assert pnr.passengers == (
            Passenger(1, "POPESCU", "ANDREI", "MR"),
            Passenger(2, "POPESCU", "MARIA ELENA", "MRS"),
        )

    def test_title_is_optional(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1.DOE/JANE", CONTEXT)
        assert pnr.passengers == (Passenger(1, "DOE", "JANE", None),)

    def test_extracts_record_locator_from_header(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "basic_return"), CONTEXT)
        assert pnr.record_locator == "ZX7K2P"

    def test_missing_header_gives_no_record_locator(self, parser: AmadeusParser) -> None:
        assert parser.parse("  1.DOE/JANE", CONTEXT).record_locator is None
