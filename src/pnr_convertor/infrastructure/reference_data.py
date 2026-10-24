"""Reference data adapters backed by bundled datasets, loaded once at startup."""

from __future__ import annotations

import json
from importlib.resources import files

import airportsdata

from pnr_convertor.domain.reference import Airline, Airport

# airportsdata names the district before the city for these airports.
_CITY_OVERRIDES = {"IST": "Istanbul"}


class BundledAirportRepository:
    def __init__(self) -> None:
        self._airports = {
            code: Airport(
                iata=code,
                name=entry["name"],
                city=_CITY_OVERRIDES.get(code, entry["city"]) or None,
                country=entry["country"],
                timezone=entry["tz"],
                latitude=entry["lat"],
                longitude=entry["lon"],
            )
            for code, entry in airportsdata.load("IATA").items()
        }

    def get(self, iata: str) -> Airport | None:
        return self._airports.get(iata)


class BundledAirlineRepository:
    def __init__(self) -> None:
        raw = (files("pnr_convertor") / "data" / "airlines.json").read_text(encoding="utf-8")
        names: dict[str, str] = json.loads(raw)
        self._airlines = {code: Airline(iata=code, name=name) for code, name in names.items()}

    def get(self, iata: str) -> Airline | None:
        return self._airlines.get(iata)
