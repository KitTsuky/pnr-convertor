from __future__ import annotations

from datetime import date

import pytest

from pnr_convertor.domain.models import Passenger, Ticket
from pnr_convertor.parsing.travelport import read_electronic_tickets

JANE = Passenger(1, "DOE", "JANE", "MRS")
JOHN = Passenger(2, "DOE", "JOHN PAUL", "MR")


def test_reads_the_ticket_block() -> None:
    text = (
        "TKT: 081 9615 526990     NAME: DOE/JANEMRS\n"
        " CC: CAXXXXXXXXXXX0000\n"
        "ISSUED: 19NOV25          FOP:CK\n"
        "PSEUDO: 1O3K  PLATING CARRIER: QF  ISO: AU  IATA: 05578602"
    )
    assert read_electronic_tickets(text, [JANE, JOHN]) == (
        Ticket("081-9615526990", 1, "QF", date(2025, 11, 19), electronic=True),
    )


@pytest.mark.parametrize(
    "line",
    [
        "TKT: 0819615526990 NAME: DOE/JANEMRS",
        "TKT: 081 9615 526990-991 NAME: DOE/JANEMRS",
        "  TKT:081 9615526990  NAME: DOE/JANEMRS",
    ],
)
def test_number_layouts(line: str) -> None:
    (ticket,) = read_electronic_tickets(line, [JANE])
    assert ticket.number == "081-9615526990"


def test_name_with_several_given_names_matches_its_passenger() -> None:
    (ticket,) = read_electronic_tickets("TKT: 081 9615 526990 NAME: DOE/JOHNPAULMR", [JANE, JOHN])
    assert ticket.passenger_index == 2


def test_unknown_name_is_left_unassigned_with_several_passengers() -> None:
    (ticket,) = read_electronic_tickets("TKT: 081 9615 526990 NAME: ROE/ANNMS", [JANE, JOHN])
    assert ticket.passenger_index is None


def test_unknown_name_belongs_to_the_only_passenger() -> None:
    (ticket,) = read_electronic_tickets("TKT: 081 9615 526990 NAME: DOE/JANEMS", [JANE])
    assert ticket.passenger_index == 1


def test_malformed_issue_date_is_dropped() -> None:
    text = "TKT: 081 9615 526990 NAME: DOE/JANEMRS\nISSUED: 31APR25"
    (ticket,) = read_electronic_tickets(text, [JANE])
    assert ticket.issue_date is None


def test_details_before_any_ticket_are_ignored() -> None:
    text = "ISSUED: 19NOV25\nPSEUDO: 1O3K  PLATING CARRIER: QF"
    assert read_electronic_tickets(text, [JANE]) == ()
