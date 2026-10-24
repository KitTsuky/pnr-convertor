"""Electronic ticket display (`*HTE`), identical in Galileo and Apollo, e.g.:

TKT: 081 9615 526990     NAME: DOE/JANEMRS
 CC: CAXXXXXXXXXXX4697
ISSUED: 19NOV25          FOP:CK
PSEUDO: 1O3K  PLATING CARRIER: QF  ISO: AU  IATA: 05578602
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import date

from pnr_convertor.domain.models import Passenger, Ticket
from pnr_convertor.parsing.dates import parse_full_date

# A conjunction ticket shows the last number's final digits after a dash (`828264-265`).
_TICKET = re.compile(
    r"^\s*TKT:\s*(?P<number>\d{3}\s?\d{4}\s?\d{6})(?:-\d{1,3})?\s+NAME:\s*(?P<name>\S+)"
)
_ISSUED = re.compile(r"^\s*ISSUED:\s*(?P<date>\d{2}[A-Z]{3}\d{2})\b")
_PLATING_CARRIER = re.compile(r"\bPLATING CARRIER:\s*(?P<carrier>[A-Z0-9]{2})\b")


def read_electronic_tickets(text: str, passengers: Sequence[Passenger]) -> tuple[Ticket, ...]:
    tickets: list[Ticket] = []
    for line in text.splitlines():
        if ticket := _TICKET.match(line):
            tickets.append(_build_ticket(ticket, passengers))
        elif tickets and (issued := _ISSUED.match(line)):
            tickets[-1] = replace(tickets[-1], issue_date=_issue_date(issued["date"]))
        elif tickets and (plating := _PLATING_CARRIER.search(line)):
            tickets[-1] = replace(tickets[-1], issuing_airline=plating["carrier"])
    return tuple(tickets)


def _build_ticket(match: re.Match[str], passengers: Sequence[Passenger]) -> Ticket:
    number = match["number"].replace(" ", "")
    return Ticket(
        number=f"{number[:3]}-{number[3:]}",
        passenger_index=_holder(match["name"], passengers),
        issuing_airline=None,
        issue_date=None,
        electronic=True,
    )


def _holder(name: str, passengers: Sequence[Passenger]) -> int | None:
    """The ticket shows the name as booked, title glued: `DOE/JANEMRS`."""
    holders = [p.index for p in passengers if _ticket_name(p) == name]
    if len(holders) == 1:
        return holders[0]
    return passengers[0].index if len(passengers) == 1 else None


def _ticket_name(passenger: Passenger) -> str:
    return f"{passenger.last_name}/{passenger.first_name}{passenger.title or ''}".replace(" ", "")


def _issue_date(token: str) -> date | None:
    try:
        return parse_full_date(token)
    except ValueError:
        return None
