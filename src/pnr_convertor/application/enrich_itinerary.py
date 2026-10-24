from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pnr_convertor.application.ports import AirlineRepository, AirportRepository
from pnr_convertor.domain.itinerary import EnrichedSegment, Itinerary, Journey
from pnr_convertor.domain.models import FlightSegment, ParsedPnr, SegmentStatusCategory
from pnr_convertor.domain.reference import Airport

# Industry convention: a break longer than 24 hours is a stopover, i.e. a new journey.
STOPOVER_THRESHOLD = timedelta(hours=24)


class ItineraryEnricher:
    def __init__(
        self,
        airports: AirportRepository,
        airlines: AirlineRepository,
        *,
        stopover_threshold: timedelta = STOPOVER_THRESHOLD,
    ) -> None:
        self._airports = airports
        self._airlines = airlines
        self._stopover_threshold = stopover_threshold

    def enrich(self, pnr: ParsedPnr) -> Itinerary:
        segments = tuple(self._enrich_segment(segment) for segment in pnr.segments)
        return Itinerary(pnr=pnr, segments=segments, journeys=self._group_journeys(segments))

    def _enrich_segment(self, segment: FlightSegment) -> EnrichedSegment:
        origin = self._airports.get(segment.origin)
        destination = self._airports.get(segment.destination)
        return EnrichedSegment(
            segment=segment,
            airline=self._airlines.get(segment.carrier),
            origin=origin,
            destination=destination,
            departure_at=_localize(segment.departure, origin),
            arrival_at=_localize(segment.arrival, destination),
        )

    def _group_journeys(self, segments: tuple[EnrichedSegment, ...]) -> tuple[Journey, ...]:
        journeys: list[list[EnrichedSegment]] = []
        for current in segments:
            if current.segment.status.category is SegmentStatusCategory.CANCELLED:
                continue
            if journeys and not self._is_stopover(journeys[-1][-1], current):
                journeys[-1].append(current)
            else:
                journeys.append([current])
        return tuple(Journey(tuple(journey)) for journey in journeys)

    def _is_stopover(self, inbound: EnrichedSegment, outbound: EnrichedSegment) -> bool:
        if inbound.arrival_at and outbound.departure_at:
            gap = outbound.departure_at - inbound.arrival_at
        else:
            # Without timezones, local times are off by at most a day: good enough for 24h.
            gap = outbound.segment.departure - inbound.segment.arrival
        return gap > self._stopover_threshold


def _localize(local: datetime, airport: Airport | None) -> datetime | None:
    if airport is None:
        return None
    return local.replace(tzinfo=ZoneInfo(airport.timezone))
