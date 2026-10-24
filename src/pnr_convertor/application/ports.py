from __future__ import annotations

from datetime import date
from typing import Protocol

from pnr_convertor.domain.reference import Airline, Airport


class Clock(Protocol):
    def today(self) -> date: ...


class AirportRepository(Protocol):
    def get(self, iata: str) -> Airport | None: ...


class AirlineRepository(Protocol):
    def get(self, iata: str) -> Airline | None: ...
