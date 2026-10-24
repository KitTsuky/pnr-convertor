from __future__ import annotations

from datetime import date, datetime

import pytest

from pnr_convertor.domain.models import Contact, ContactKind, Passenger, Ticket
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.worldspan import WorldspanParser
from tests.conftest import REFERENCE_DATE, read_fixture

CONTEXT = ParseContext(reference_date=REFERENCE_DATE)


@pytest.fixture
def parser() -> WorldspanParser:
    return WorldspanParser()


class TestDetect:
    def test_header_gives_full_confidence(self, parser: WorldspanParser) -> None:
        assert parser.detect(read_fixture("worldspan", "ticketed_overnight_connections")) == 1.0

    def test_segment_without_header(self, parser: WorldspanParser) -> None:
        assert parser.detect(" 1 QR 633J 21AUG SA ISBDOH SS1  0415  0555 /O $ J01 E") == 0.8

    @pytest.mark.parametrize(
        ("gds", "name"),
        [
            ("amadeus", "basic_return"),
            ("sabre", "next_day_arrival"),
            ("galileo", "booking_file_connections"),
        ],
    )
    def test_other_formats_are_not_recognized(
        self, parser: WorldspanParser, gds: str, name: str
    ) -> None:
        assert parser.detect(read_fixture(gds, name)) == 0.0


class TestSegments:
    def test_parses_all_fields(self, parser: WorldspanParser) -> None:
        line = " 3 KL 644Y 12DEC FR JFKAMS HK1  1830  0745 #1/O $ E"
        (segment,) = parser.parse(line, CONTEXT).segments

        assert (segment.carrier, segment.flight_number, segment.booking_class) == ("KL", "644", "Y")
        assert (segment.origin, segment.destination) == ("JFK", "AMS")
        assert segment.departure == datetime(2025, 12, 12, 18, 30)
        assert segment.arrival == datetime(2025, 12, 13, 7, 45)
        assert (segment.status.code, segment.passenger_count) == ("HK", 1)

    @pytest.mark.parametrize(
        "line",
        [
            pytest.param(" 1 RO1381Y 05DEC FR OTPAMS HK1  0715  0905 /O $", id="carrier-glued"),
            pytest.param(" 1 RO 381Y 05DEC FR OTPAMS SS1  0715  0905 /X $ J01 E", id="extras"),
            pytest.param(" 1 RO 381Y 05DEC FR OTPAMS HK1 715A 905A/O", id="12-hour-compact"),
            pytest.param(
                "1.   RO  381Y  05DEC  FR  OTPAMS  HK1  0715  0905  /O  $  E", id="spaced"
            ),
        ],
    )
    def test_display_variants(self, parser: WorldspanParser, line: str) -> None:
        (segment,) = parser.parse(line, CONTEXT).segments
        assert segment.origin == "OTP"
        assert segment.departure.time().hour == 7

    def test_invalid_segment_is_skipped_with_warning(self, parser: WorldspanParser) -> None:
        text = (
            " 1 RO 381Y 31APR FR OTPAMS HK1  0715  0905 /O $ E\n"
            " 2 RO 382Y 13DEC SA AMSOTP HK1  1000  1405 /O $ E"
        )
        pnr = parser.parse(text, CONTEXT)
        assert [s.index for s in pnr.segments] == [2]
        assert pnr.warnings[0].line_number == 1


class TestFields:
    def test_record_locator(self, parser: WorldspanParser) -> None:
        pnr = parser.parse(read_fixture("worldspan", "ticketed_overnight_connections"), CONTEXT)
        assert pnr.record_locator == "7KQ2ZX"

    @pytest.mark.parametrize(
        ("item", "expected"),
        [
            ("1.1POPESCU/ANDREI.MR*ADT", Passenger(1, "POPESCU", "ANDREI", "MR", "ADT")),
            ("1.1DOE/AMS*ADT", Passenger(1, "DOE", "A", "MS", "ADT")),
            ("1.1DOE/SMRS*ADT", Passenger(1, "DOE", "S", "MRS", "ADT")),
            ("2.1DOE/LUCA@*CNN", Passenger(2, "DOE", "LUCA", None, "CNN")),
            ("3.1DOE/SARA@*INF", Passenger(3, "DOE", "SARA", None, "INF")),
            ("1.1IVANOV/ALEXANDR*ADT", Passenger(1, "IVANOV", "ALEXANDR", None, "ADT")),
        ],
    )
    def test_names(self, parser: WorldspanParser, item: str, expected: Passenger) -> None:
        assert parser.parse(f" {item}", CONTEXT).passengers == (expected,)

    def test_several_names_on_one_line(self, parser: WorldspanParser) -> None:
        pnr = parser.parse(" 1.1DOE/ANA.MRS*ADT  2.1DOE/LUCA@*CNN", CONTEXT)
        assert [p.index for p in pnr.passengers] == [1, 2]

    def test_phone_field(self, parser: WorldspanParser) -> None:
        pnr = parser.parse(read_fixture("worldspan", "ticketed_overnight_connections"), CONTEXT)
        assert pnr.contacts == (
            Contact(ContactKind.PHONE, "BUH 021 555-0100-B/TEST TRAVEL/ REF ANA"),
        )

    def test_electronic_and_paper_tickets(self, parser: WorldspanParser) -> None:
        electronic = parser.parse(
            " 1.1DOE/ANA*ADT\nT- 1.T/14OCT1530  1P/BUH/AN*E2811234567890", CONTEXT
        )
        paper = parser.parse(" 1.1DOE/ANA*ADT\nT- 1.T/14OCT1530  1P/BUH/AN*1911234567890", CONTEXT)

        assert electronic.tickets == (Ticket("281-1234567890", 1, None, None, electronic=True),)
        assert paper.tickets[0].electronic is False

    def test_ticketing_time_limit_is_not_a_ticket(self, parser: WorldspanParser) -> None:
        pnr = parser.parse(read_fixture("worldspan", "family_child_infant_waitlist"), CONTEXT)
        assert pnr.tickets == ()

    def test_numbered_continuation_lines_stay_in_their_field(self, parser: WorldspanParser) -> None:
        text = "P- 1.BUH 021 555-0100-B/TEST\n   2.BUH 0700 000 000-H\nT- 1.TAW/00/10JAN"
        pnr = parser.parse(text, CONTEXT)
        assert [c.text for c in pnr.contacts] == ["BUH 021 555-0100-B/TEST", "BUH 0700 000 000-H"]

    def test_weekday_identifies_the_year(self, parser: WorldspanParser) -> None:
        line = " 1 UA 957Q 01NOV MO LHRJFK HK1  0900  1210 /O $ E"
        (segment,) = parser.parse(line, ParseContext(reference_date=date(2026, 10, 24))).segments
        assert segment.departure.date() == date(2027, 11, 1)
