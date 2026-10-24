"""GDS-agnostic PNR model produced by every parser and consumed by every later stage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class GdsFormat(StrEnum):
    AMADEUS = "amadeus"
    SABRE = "sabre"
    GALILEO = "galileo"
    WORLDSPAN = "worldspan"
    APOLLO = "apollo"


class SegmentStatusCategory(StrEnum):
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    REQUESTED = "requested"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


_STATUS_CATEGORIES: dict[str, SegmentStatusCategory] = {
    "HK": SegmentStatusCategory.CONFIRMED,
    "KK": SegmentStatusCategory.CONFIRMED,
    "KL": SegmentStatusCategory.CONFIRMED,
    "TK": SegmentStatusCategory.CONFIRMED,
    "RR": SegmentStatusCategory.CONFIRMED,
    "SS": SegmentStatusCategory.CONFIRMED,
    "HS": SegmentStatusCategory.CONFIRMED,
    "DK": SegmentStatusCategory.CONFIRMED,
    "HL": SegmentStatusCategory.WAITLISTED,
    "LL": SegmentStatusCategory.WAITLISTED,
    "TL": SegmentStatusCategory.WAITLISTED,
    "HN": SegmentStatusCategory.REQUESTED,
    "NN": SegmentStatusCategory.REQUESTED,
    "PN": SegmentStatusCategory.REQUESTED,
    "HX": SegmentStatusCategory.CANCELLED,
    "XX": SegmentStatusCategory.CANCELLED,
    "UN": SegmentStatusCategory.CANCELLED,
    "UC": SegmentStatusCategory.CANCELLED,
    "NO": SegmentStatusCategory.CANCELLED,
}


_STATUS_DESCRIPTIONS: dict[str, str] = {
    "HK": "Holding confirmed",
    "KK": "Confirmed by airline",
    "KL": "Confirmed from waitlist",
    "TK": "Confirmed after schedule change",
    "RR": "Reconfirmed",
    "SS": "Sold",
    "HS": "Holding sold",
    "GK": "Passive segment",
    "HL": "Holding waitlisted",
    "LL": "Waitlisted",
    "TL": "Waitlisted after schedule change",
    "HN": "Holding need",
    "NN": "Need",
    "PN": "Pending confirmation",
    "HX": "Holding cancelled",
    "XX": "Cancelled",
    "UN": "Unable, flight does not operate",
    "UC": "Unable, waitlist closed",
    "NO": "No action taken",
    "WK": "Was confirmed, replaced by schedule change",
}


@dataclass(frozen=True, slots=True)
class SegmentStatus:
    code: str

    @property
    def category(self) -> SegmentStatusCategory:
        return _STATUS_CATEGORIES.get(self.code, SegmentStatusCategory.UNKNOWN)

    @property
    def description(self) -> str | None:
        return _STATUS_DESCRIPTIONS.get(self.code)


@dataclass(frozen=True, slots=True)
class Infant:
    """An infant travelling on an adult's lap, without a seat or a passenger number."""

    last_name: str
    first_name: str
    date_of_birth: date | None


@dataclass(frozen=True, slots=True)
class Passenger:
    """`type_code` is the GDS passenger type: ADT, CHD, INS (infant with a seat), ..."""

    index: int
    last_name: str
    first_name: str
    title: str | None = None
    type_code: str = "ADT"
    date_of_birth: date | None = None
    infant: Infant | None = None


@dataclass(frozen=True, slots=True)
class FlightSegment:
    """`departure` and `arrival` are naive, in each airport's local time."""

    index: int
    carrier: str
    flight_number: str
    booking_class: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    status: SegmentStatus
    passenger_count: int


@dataclass(frozen=True, slots=True)
class Ticket:
    number: str
    passenger_index: int | None
    issuing_airline: str | None
    issue_date: date | None
    electronic: bool
    infant: bool = False


@dataclass(frozen=True, slots=True)
class SeatAssignment:
    segment_index: int
    passenger_index: int | None
    seat: str


class ContactKind(StrEnum):
    PHONE = "phone"
    EMAIL = "email"


@dataclass(frozen=True, slots=True)
class Contact:
    """Free-text contact element, kept verbatim (GDS prefixes such as city codes included)."""

    kind: ContactKind
    text: str


@dataclass(frozen=True, slots=True)
class ParseWarning:
    """Non-fatal parsing problem. Must never contain raw PNR text."""

    line_number: int
    message: str


@dataclass(frozen=True, slots=True)
class ParsedPnr:
    gds: GdsFormat
    record_locator: str | None
    passengers: tuple[Passenger, ...]
    segments: tuple[FlightSegment, ...]
    warnings: tuple[ParseWarning, ...] = ()
    tickets: tuple[Ticket, ...] = ()
    seats: tuple[SeatAssignment, ...] = ()
    contacts: tuple[Contact, ...] = ()
