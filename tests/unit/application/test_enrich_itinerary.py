from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pnr_convertor.application.enrich_itinerary import ItineraryEnricher
from pnr_convertor.domain.models import FlightSegment, GdsFormat, ParsedPnr
from tests.factories import (
    AIRLINES,
    AIRPORTS,
    InMemoryAirlineRepository,
    InMemoryAirportRepository,
    make_segment,
)


@pytest.fixture
def enricher() -> ItineraryEnricher:
    return ItineraryEnricher(InMemoryAirportRepository(), InMemoryAirlineRepository())


def _pnr(*segments: FlightSegment) -> ParsedPnr:
    return ParsedPnr(GdsFormat.AMADEUS, None, (), segments)


def test_resolves_reference_data(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20"))
    )

    (segment,) = itinerary.segments
    assert segment.airline == AIRLINES["RO"]
    assert segment.origin == AIRPORTS["OTP"]
    assert segment.destination == AIRPORTS["CDG"]


def test_converts_local_times_using_airport_timezones(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20"))
    )

    (segment,) = itinerary.segments
    assert segment.departure_at == datetime(2026, 3, 15, 5, 10, tzinfo=UTC)
    assert segment.arrival_at == datetime(2026, 3, 15, 8, 20, tzinfo=UTC)
    assert segment.duration == timedelta(hours=3, minutes=10)


def test_handles_daylight_saving_change(enricher: ItineraryEnricher) -> None:
    # Europe switches to summer time on 29 March 2026; New York already switched on 8 March.
    itinerary = enricher.enrich(
        _pnr(make_segment("LHR", "JFK", "2026-03-29T11:20", "2026-03-29T14:30"))
    )
    assert itinerary.segments[0].duration == timedelta(hours=8, minutes=10)


def test_unknown_airport_leaves_times_and_duration_unknown(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(make_segment("OTP", "ZZZ", "2026-03-15T07:10", "2026-03-15T09:20"))
    )

    (segment,) = itinerary.segments
    assert segment.destination is None
    assert segment.arrival_at is None
    assert segment.duration is None


def test_unknown_airline(enricher: ItineraryEnricher) -> None:
    segment = make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", carrier="ZZ")
    assert enricher.enrich(_pnr(segment)).segments[0].airline is None


def test_connections_within_24_hours_form_one_journey(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(
            make_segment("LHR", "JFK", "2025-12-28T11:20", "2025-12-28T14:30", index=1),
            make_segment("JFK", "DXB", "2025-12-28T23:00", "2025-12-29T19:30", index=2),
        )
    )

    (journey,) = itinerary.journeys
    assert (journey.origin, journey.destination) == ("LHR", "DXB")
    (connection,) = journey.connections
    assert connection.airport == "JFK"
    assert connection.duration == timedelta(hours=8, minutes=30)


def test_stopover_longer_than_24_hours_starts_a_new_journey(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(
            make_segment("OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=1),
            make_segment("CDG", "OTP", "2026-03-22T19:45", "2026-03-22T23:50", index=2),
        )
    )

    assert [(j.origin, j.destination) for j in itinerary.journeys] == [
        ("OTP", "CDG"),
        ("CDG", "OTP"),
    ]


def test_stopover_falls_back_to_local_times_without_timezones(enricher: ItineraryEnricher) -> None:
    itinerary = enricher.enrich(
        _pnr(
            make_segment("OTP", "ZZZ", "2026-03-15T07:10", "2026-03-15T09:20", index=1),
            make_segment("ZZZ", "CDG", "2026-03-15T12:00", "2026-03-15T14:00", index=2),
            make_segment("CDG", "OTP", "2026-03-20T19:45", "2026-03-20T23:50", index=3),
        )
    )

    assert [len(j.segments) for j in itinerary.journeys] == [2, 1]


def test_cancelled_segments_are_kept_but_excluded_from_journeys(
    enricher: ItineraryEnricher,
) -> None:
    itinerary = enricher.enrich(
        _pnr(
            make_segment(
                "OTP", "CDG", "2026-03-15T07:10", "2026-03-15T09:20", index=1, status="HX"
            ),
            make_segment("OTP", "CDG", "2026-03-15T13:00", "2026-03-15T15:10", index=2),
        )
    )

    assert len(itinerary.segments) == 2
    (journey,) = itinerary.journeys
    assert [s.segment.index for s in journey.segments] == [2]
