from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Airport:
    iata: str
    name: str
    city: str | None
    country: str
    timezone: str


@dataclass(frozen=True, slots=True)
class Airline:
    iata: str
    name: str
