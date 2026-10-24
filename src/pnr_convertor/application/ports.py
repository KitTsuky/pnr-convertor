from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Protocol

from pnr_convertor.domain.itinerary import Itinerary
from pnr_convertor.domain.reference import Airline, Airport


class Clock(Protocol):
    def today(self) -> date: ...


class AirportRepository(Protocol):
    def get(self, iata: str) -> Airport | None: ...


class AirlineRepository(Protocol):
    def get(self, iata: str) -> Airline | None: ...


class RenderFormat(StrEnum):
    TEXT = "text"
    HTML = "html"


class ItineraryRenderer(Protocol):
    @property
    def format(self) -> RenderFormat: ...

    @property
    def media_type(self) -> str: ...

    def render(self, itinerary: Itinerary) -> str: ...
