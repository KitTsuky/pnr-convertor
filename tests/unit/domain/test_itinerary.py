from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from pnr_convertor.domain.itinerary import Connection, EnrichedSegment, Journey
from tests.factories import AIRPORTS, make_segment


def _enriched(
    origin: str, destination: str, departure: datetime | None, arrival: datetime | None
) -> EnrichedSegment:
    segment = make_segment(origin, destination, "2026-03-15T07:00", "2026-03-15T09:00")
    return EnrichedSegment(segment, None, None, None, departure, arrival)


def _utc(hour: int, day: int = 15) -> datetime:
    return datetime(2026, 3, day, hour, tzinfo=UTC)


def test_segment_duration() -> None:
    assert _enriched("OTP", "CDG", _utc(5), _utc(8)).duration == timedelta(hours=3)


def test_segment_duration_is_unknown_without_times() -> None:
    assert _enriched("OTP", "CDG", None, _utc(8)).duration is None


def test_negative_duration_is_treated_as_unknown() -> None:
    assert _enriched("OTP", "CDG", _utc(8), _utc(5)).duration is None


def test_journey_spans_first_departure_to_last_arrival() -> None:
    journey = Journey(
        (
            _enriched("OTP", "CDG", _utc(5), _utc(8)),
            _enriched("CDG", "JFK", _utc(10), _utc(18)),
        )
    )

    assert (journey.origin, journey.destination) == ("OTP", "JFK")
    assert journey.departure_at == _utc(5)
    assert journey.arrival_at == _utc(18)
    assert journey.duration == timedelta(hours=13)
    assert journey.connections == (Connection(airport="CDG", duration=timedelta(hours=2)),)


def test_single_segment_journey_has_no_connections() -> None:
    assert Journey((_enriched("OTP", "CDG", _utc(5), _utc(8)),)).connections == ()


def test_segment_distance_requires_both_airports() -> None:
    segment = make_segment("OTP", "CDG", "2026-03-15T07:00", "2026-03-15T09:00")
    known = EnrichedSegment(segment, None, AIRPORTS["OTP"], AIRPORTS["CDG"], None, None)
    unknown = EnrichedSegment(segment, None, AIRPORTS["OTP"], None, None, None)

    assert known.distance_km == pytest.approx(1856.3, abs=0.1)
    assert unknown.distance_km is None


def test_journey_distance_sums_segments_only_when_all_known() -> None:
    first = make_segment("OTP", "CDG", "2026-03-15T07:00", "2026-03-15T09:00")
    second = make_segment("CDG", "JFK", "2026-03-15T11:00", "2026-03-15T13:00")
    leg_one = EnrichedSegment(first, None, AIRPORTS["OTP"], AIRPORTS["CDG"], None, None)
    leg_two = EnrichedSegment(second, None, AIRPORTS["CDG"], AIRPORTS["JFK"], None, None)
    unknown = EnrichedSegment(second, None, AIRPORTS["CDG"], None, None, None)

    total = Journey((leg_one, leg_two)).distance_km
    assert total == pytest.approx(leg_one.distance_km + leg_two.distance_km)  # type: ignore[operator]
    assert Journey((leg_one, unknown)).distance_km is None
