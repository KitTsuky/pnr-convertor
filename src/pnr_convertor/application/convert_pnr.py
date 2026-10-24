from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from pnr_convertor.application.enrich_itinerary import ItineraryEnricher
from pnr_convertor.application.ports import Clock
from pnr_convertor.domain.errors import PnrParseError
from pnr_convertor.domain.itinerary import Itinerary
from pnr_convertor.domain.models import GdsFormat
from pnr_convertor.parsing.base import ParseContext
from pnr_convertor.parsing.registry import ParserRegistry
from pnr_convertor.parsing.text import normalize_pnr_text

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConvertPnrCommand:
    text: str
    gds: GdsFormat | None = None
    reference_date: date | None = None


class ConvertPnr:
    def __init__(self, registry: ParserRegistry, enricher: ItineraryEnricher, clock: Clock) -> None:
        self._registry = registry
        self._enricher = enricher
        self._clock = clock

    def execute(self, command: ConvertPnrCommand) -> Itinerary:
        text = normalize_pnr_text(command.text)
        parser = self._registry.resolve(text, command.gds)
        context = ParseContext(reference_date=command.reference_date or self._clock.today())

        pnr = parser.parse(text, context)
        if not pnr.segments:
            raise PnrParseError("No flight segments were found in the PNR")
        itinerary = self._enricher.enrich(pnr)

        # PNRs contain personal data: log shape and counts only, never content.
        logger.info(
            "pnr_converted",
            extra={
                "gds": pnr.gds,
                "segments": len(pnr.segments),
                "passengers": len(pnr.passengers),
                "journeys": len(itinerary.journeys),
                "warnings": len(pnr.warnings),
            },
        )
        return itinerary
