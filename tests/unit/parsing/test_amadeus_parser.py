from __future__ import annotations

from datetime import date, datetime

import pytest

from pnr_convertor.domain.models import (
    Contact,
    ContactKind,
    Infant,
    Passenger,
    SeatAssignment,
    SegmentStatusCategory,
    Ticket,
)
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

    def test_asterisk_after_weekday_and_12_hour_times(self, parser: AmadeusParser) -> None:
        line = "  4  BA 179 T 20APR 7*JFKLHR HK2   745P  750A 21APR  E  BA/9XZABC"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert (segment.origin, segment.destination) == ("JFK", "LHR")
        assert segment.departure == datetime(2025, 4, 20, 19, 45)
        assert segment.arrival == datetime(2025, 4, 21, 7, 50)

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

    def test_weekday_identifies_year_of_an_old_pnr(self, parser: AmadeusParser) -> None:
        text = (
            "  1  RO 391 Y 05JUN 4 OTPCDG HK1  0710 0920\n"
            "  2  RO 392 Y 25JUL 5 CDGOTP HK1  1945 2350"
        )
        pnr = parser.parse(text, ParseContext(reference_date=date(2026, 10, 24)))
        assert [s.departure.date() for s in pnr.segments] == [date(2025, 6, 5), date(2025, 7, 25)]

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

    @pytest.mark.parametrize(
        ("line", "expected"),
        [
            ("  1.SMITH/JOHNMR   2.BROWN/ANNAMS", [("JOHN", "MR"), ("ANNA", "MS")]),
            ("  1.DOE/JANEMRS", [("JANE", "MRS")]),
            ("  1.IVANOV/ALEXANDR", [("ALEXANDR", None)]),
            ("  1.WHO/JOHN DR", [("JOHN", "DR")]),
        ],
    )
    def test_titles_glued_to_first_name(
        self, parser: AmadeusParser, line: str, expected: list[tuple[str, str | None]]
    ) -> None:
        pnr = parser.parse(line, CONTEXT)
        assert [(p.first_name, p.title) for p in pnr.passengers] == expected

    def test_title_is_optional(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1.DOE/JANE", CONTEXT)
        assert pnr.passengers == (Passenger(1, "DOE", "JANE", None),)

    def test_extracts_record_locator_from_header(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "basic_return"), CONTEXT)
        assert pnr.record_locator == "ZX7K2P"

    def test_missing_header_gives_no_record_locator(self, parser: AmadeusParser) -> None:
        assert parser.parse("  1.DOE/JANE", CONTEXT).record_locator is None


class TestTicketsSeatsAndContacts:
    def test_tickets(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "ticketed_with_seats_and_contacts"), CONTEXT)
        assert pnr.tickets == (
            Ticket("125-9876543210", 1, "BA", date(2025, 3, 30), electronic=True),
            Ticket("125-9876543211", 2, "BA", date(2025, 3, 30), electronic=True),
        )

    def test_seats_are_linked_to_segment_and_passenger(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "ticketed_with_seats_and_contacts"), CONTEXT)
        assert [(s.segment_index, s.passenger_index, s.seat) for s in pnr.seats] == [
            (3, 1, "12A"),
            (3, 2, "12B"),
            (4, 1, "14C"),
            (4, 2, "14D"),
        ]

    def test_contacts_are_kept_verbatim(self, parser: AmadeusParser) -> None:
        pnr = parser.parse(read_fixture("amadeus", "ticketed_with_seats_and_contacts"), CONTEXT)
        assert pnr.contacts == (
            Contact(ContactKind.PHONE, "LON020 7946 1234"),
            Contact(ContactKind.EMAIL, "LONTRAVEL@EXAMPLE.COM"),
            Contact(ContactKind.EMAIL, "J.SMITH@EXAMPLE.COM"),
        )

    def test_unreferenced_elements_belong_to_the_only_passenger(
        self, parser: AmadeusParser
    ) -> None:
        text = (
            "  1.DOE/JANE MS\n"
            "  2  RO 391 Y 15MAR OTPCDG HK1  0710 0920\n"
            "  3 SSR RQST RO HK1 OTPCDG/7C/S2\n"
            "  4 FA PAX 281-1234567890/ETRO/10JAN26/BUHRO08AA/12345678"
        )
        pnr = parser.parse(text, CONTEXT)
        assert pnr.seats == (SeatAssignment(segment_index=2, passenger_index=1, seat="7C"),)
        assert pnr.tickets[0].passenger_index == 1

    def test_paper_ticket_without_issue_date(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1.DOE/JANE\n  2 FA PAX 125-1234567890/BA", CONTEXT)
        assert pnr.tickets == (Ticket("125-1234567890", 1, "BA", None, electronic=False),)

    def test_invalid_ticket_date_becomes_warning(self, parser: AmadeusParser) -> None:
        pnr = parser.parse("  1.DOE/JANE\n  2 FA PAX 125-1234567890/ETBA/31APR25/X", CONTEXT)
        assert pnr.tickets == ()
        assert pnr.warnings[0].line_number == 2


class TestChildrenAndInfants:
    def test_child_with_date_of_birth(self, parser: AmadeusParser) -> None:
        (child,) = parser.parse("  1.POPESCU/IOANA MS(CHD/05APR19)", CONTEXT).passengers
        assert (child.first_name, child.title) == ("IOANA", "MS")
        assert (child.type_code, child.date_of_birth) == ("CHD", date(2019, 4, 5))

    def test_infant_with_seat(self, parser: AmadeusParser) -> None:
        (infant,) = parser.parse("  1.STAN/DARIA(INS)", CONTEXT).passengers
        assert (infant.first_name, infant.type_code, infant.date_of_birth) == ("DARIA", "INS", None)

    def test_lap_infant_shares_the_adult_surname(self, parser: AmadeusParser) -> None:
        (adult,) = parser.parse("  1.POPESCU/ANDREI MR(INF/ILINCA/14JAN24)", CONTEXT).passengers
        assert adult.type_code == "ADT"
        assert adult.infant == Infant("POPESCU", "ILINCA", date(2024, 1, 14))

    def test_lap_infant_with_another_surname(self, parser: AmadeusParser) -> None:
        (adult,) = parser.parse("  1.IONESCU/ELENA(INFVASILE/MATEI/20FEB24)", CONTEXT).passengers
        assert adult.infant == Infant("VASILE", "MATEI", date(2024, 2, 20))

    def test_lap_infant_without_date_of_birth(self, parser: AmadeusParser) -> None:
        (adult,) = parser.parse("  1.DOE/JANE(INF/KEVIN)", CONTEXT).passengers
        assert adult.infant == Infant("DOE", "KEVIN", None)

    def test_unknown_qualifier_is_ignored(self, parser: AmadeusParser) -> None:
        (passenger,) = parser.parse("  1.DOE/JANE(XYZ123)", CONTEXT).passengers
        assert passenger == Passenger(1, "DOE", "JANE")

    def test_invalid_date_of_birth_is_dropped(self, parser: AmadeusParser) -> None:
        (child,) = parser.parse("  1.DOE/ANA(CHD/31APR19)", CONTEXT).passengers
        assert (child.type_code, child.date_of_birth) == ("CHD", None)

    def test_infant_ticket(self, parser: AmadeusParser) -> None:
        text = (
            "  1.POPESCU/ANDREI MR(INF/ILINCA/14JAN24)\n"
            "  2 FA PAX 281-1234567890/ETRO/14MAR25/BUHRO08AA/12345678/P1\n"
            "  3 FA INF 281-1234567891/ETRO/14MAR25/BUHRO08AA/12345678/P1"
        )
        pnr = parser.parse(text, CONTEXT)
        assert [(t.passenger_index, t.infant) for t in pnr.tickets] == [(1, False), (1, True)]
