"""Reference data adapters backed by bundled datasets, loaded once at startup."""

from __future__ import annotations

import json
import re
from collections.abc import Collection
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
    def __init__(self, *, logo_codes: Collection[str] = ()) -> None:
        raw = (files("pnr_convertor") / "data" / "airlines.json").read_text(encoding="utf-8")
        names: dict[str, str] = json.loads(raw)
        self._airlines = {
            code: Airline(iata=code, name=name, has_logo=code in logo_codes)
            for code, name in names.items()
        }

    def get(self, iata: str) -> Airline | None:
        return self._airlines.get(iata)


_IATA_CODE = re.compile(r"[A-Z0-9]{2}")


class BundledAirlineLogoRepository:
    """Bundled PNG logos from Wikimedia Commons; `manifest.json` records each source and license."""

    def __init__(self) -> None:
        self._directory = files("pnr_convertor") / "data" / "airline_logos"
        manifest = self._directory / "manifest.json"
        entries = (
            json.loads(manifest.read_text(encoding="utf-8"))["logos"] if manifest.is_file() else []
        )
        self.codes = frozenset(entry["code"] for entry in entries)

    def get(self, iata: str) -> bytes | None:
        # Only codes listed in the manifest are read, so the path can never escape the directory.
        if not _IATA_CODE.fullmatch(iata) or iata not in self.codes:
            return None
        return (self._directory / f"{iata}.png").read_bytes()
