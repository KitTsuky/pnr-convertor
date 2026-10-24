"""A parsed PNR enriched with reference data and timezone-aware times."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise

from pnr_convertor.domain.models import FlightSegment, ParsedPnr
from pnr_convertor.domain.reference import Airline, Airport


def _elapsed(start: datetime | None, end: datetime | None) -> timedelta | None:
    if start is None or end is None or end < start:
        return None
    return end - start


@dataclass(frozen=True, slots=True)
class EnrichedSegment:
    """`departure_at` / `arrival_at` are timezone-aware; None when an airport is unknown."""

    segment: FlightSegment
    airline: Airline | None
    origin: Airport | None
    destination: Airport | None
    departure_at: datetime | None
    arrival_at: datetime | None

    @property
    def duration(self) -> timedelta | None:
        return _elapsed(self.departure_at, self.arrival_at)


@dataclass(frozen=True, slots=True)
class Connection:
    airport: str
    duration: timedelta | None


@dataclass(frozen=True, slots=True)
class Journey:
    """Consecutive segments travelled without a stopover, e.g. the outbound leg of a trip."""

    segments: tuple[EnrichedSegment, ...]

    @property
    def origin(self) -> str:
        return self.segments[0].segment.origin

    @property
    def destination(self) -> str:
        return self.segments[-1].segment.destination

    @property
    def departure_at(self) -> datetime | None:
        return self.segments[0].departure_at

    @property
    def arrival_at(self) -> datetime | None:
        return self.segments[-1].arrival_at

    @property
    def duration(self) -> timedelta | None:
        return _elapsed(self.departure_at, self.arrival_at)

    @property
    def connections(self) -> tuple[Connection, ...]:
        return tuple(
            Connection(
                airport=inbound.segment.destination,
                duration=_elapsed(inbound.arrival_at, outbound.departure_at),
            )
            for inbound, outbound in pairwise(self.segments)
        )


@dataclass(frozen=True, slots=True)
class Itinerary:
    pnr: ParsedPnr
    segments: tuple[EnrichedSegment, ...]
    journeys: tuple[Journey, ...]
