from __future__ import annotations

from datetime import date, datetime

import pytest

from pnr_convertor.domain.models import Contact, ContactKind, Passenger
from pnr_convertor.parsing.apollo import ApolloParser
from pnr_convertor.parsing.base import ParseContext
from tests.conftest import REFERENCE_DATE, read_fixture

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)


@pytest.fixture
def parser() -> ApolloParser:
    return ApolloParser()


class TestDetect:
    def test_header_with_segments_gives_full_confidence(self, parser: ApolloParser) -> None:
        assert parser.detect(read_fixture("apollo", "overnight_codeshare_connection")) == 1.0

    def test_segment_without_header(self, parser: ApolloParser) -> None:
        assert parser.detect(" 1 UA9993S 12FEB NBOBRU HK1  1140P  645A+*  TH/FR  E  1") == 0.7

    @pytest.mark.parametrize(
        ("gds", "name"),
        [
            ("amadeus", "basic_return"),
            ("amadeus", "ticketed_with_seats_and_contacts"),
            ("sabre", "next_day_arrival"),
            ("sabre", "full_display_married_connection"),
            ("galileo", "booking_file_connections"),
            ("worldspan", "ticketed_overnight_connections"),
        ],
    )
    def test_other_formats_are_not_recognized(
        self, parser: ApolloParser, gds: str, name: str
    ) -> None:
        assert parser.detect(read_fixture(gds, name)) == 0.0


class TestSegments:
    def test_parses_all_fields(self, parser: ApolloParser) -> None:
        line = " 1 UA9993S 12FEB NBOBRU HK1  1140P  645A+*      TH/FR   E  1"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert (segment.carrier, segment.flight_number, segment.booking_class) == (
            "UA",
            "9993",
            "S",
        )
        assert (segment.origin, segment.destination) == ("NBO", "BRU")
        assert segment.departure == datetime(2026, 2, 12, 23, 40)
        assert segment.arrival == datetime(2026, 2, 13, 6, 45)
        assert (segment.status.code, segment.passenger_count) == ("HK", 1)

    @pytest.mark.parametrize(
        ("line", "arrival"),
        [
            (" 1 UA 995S 13FEB BRUEWR HK1  1115A  130P *   FR  E  1", date(2026, 2, 13)),
            (" 1 UA 995S 13FEB BRUEWR HK1  1115A  130P+  FR/SA  E", date(2026, 2, 14)),
            (" 1 UA 995S 13FEB BRUEWR HK1  1115A  130P+2 FR/SU  E", date(2026, 2, 15)),
            (" 1 UA 995S 13FEB BRUEWR HK1  1115A  130P-  FR/TH  E", date(2026, 2, 12)),
        ],
    )
    def test_arrival_day_offset(self, parser: ApolloParser, line: str, arrival: date) -> None:
        (segment,) = parser.parse(line, CONTEXT).segments
        assert segment.arrival.date() == arrival

    def test_weekday_identifies_the_year(self, parser: ApolloParser) -> None:
        friday = " 1 UA 995S 13FEB BRUEWR HK1  1115A  130P *   FR  E  1"
        saturday = " 1 UA 995S 13FEB BRUEWR HK1  1115A  130P *   SA  E  1"
        context = ParseContext(reference_date=date(2026, 10, 24))

        assert parser.parse(friday, context).segments[0].departure.date() == date(2026, 2, 13)
        assert parser.parse(saturday, context).segments[0].departure.date() == date(2027, 2, 13)

    def test_retention_and_operated_by_lines_are_not_segments(self, parser: ApolloParser) -> None:
        pnr = parser.parse(read_fixture("apollo", "overnight_codeshare_connection"), CONTEXT)
        assert [s.index for s in pnr.segments] == [1, 2]
        assert pnr.passengers == (Passenger(1, "POPESCU", "ANDREI", "MR"),)

    def test_invalid_segment_is_skipped_with_warning(self, parser: ApolloParser) -> None:
        text = (
            " 1 UA9993S 31APR NBOBRU HK1  1140P  645A+*\n"
            " 2 UA 995S 13FEB BRUEWR HK1  1115A  130P *   FR  E  1"
        )
        pnr = parser.parse(text, CONTEXT)
        assert [s.index for s in pnr.segments] == [2]
        assert pnr.warnings[0].line_number == 1


class TestFields:
    def test_record_locator(self, parser: ApolloParser) -> None:
        pnr = parser.parse(read_fixture("apollo", "family_child_infant_waitlist"), CONTEXT)
        assert pnr.record_locator == "M8RT2Q"

    @pytest.mark.parametrize(
        ("item", "expected"),
        [
            ("1.1SMITH/A MR", Passenger(1, "SMITH", "A", "MR")),
            ("1.1DOE/JOHN PAUL", Passenger(1, "DOE", "JOHN PAUL")),
            ("2.1JONES/S MS*C10", Passenger(2, "JONES", "S", "MS", "CHD")),
            ("1.1WILSON/B MR*MIL", Passenger(1, "WILSON", "B", "MR", "MIL")),
            ("1.1SMITH/CHARLES MR*12345", Passenger(1, "SMITH", "CHARLES", "MR")),
            (
                "3.I/1DOE/BABY MISS*15MAR25",
                Passenger(3, "DOE", "BABY", "MISS", "INF", date(2025, 3, 15)),
            ),
        ],
    )
    def test_names(self, parser: ApolloParser, item: str, expected: Passenger) -> None:
        assert parser.parse(f" {item}", CONTEXT).passengers == (expected,)

    def test_phone_field_with_continuation(self, parser: ApolloParser) -> None:
        pnr = parser.parse(read_fixture("apollo", "overnight_codeshare_connection"), CONTEXT)
        assert pnr.contacts == (
            Contact(ContactKind.PHONE, "SFOAS/800-555-0100 TEST TRAVEL REF ANA"),
            Contact(ContactKind.PHONE, "SFOR/415 555-0199"),
        )

    def test_other_fields_are_not_contacts(self, parser: ApolloParser) -> None:
        pnr = parser.parse("TKTG-TAU/06MAR\n  2 SFOR/415 555-0199", CONTEXT)
        assert pnr.contacts == ()
