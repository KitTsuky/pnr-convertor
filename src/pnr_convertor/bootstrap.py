"""Composition root: the only place concrete implementations are wired together."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from pnr_convertor.application.convert_pnr import ConvertPnr
from pnr_convertor.application.enrich_itinerary import ItineraryEnricher
from pnr_convertor.application.ports import Clock, ItineraryRenderer, RenderFormat
from pnr_convertor.config import Settings
from pnr_convertor.infrastructure.clock import SystemClock
from pnr_convertor.infrastructure.reference_data import (
    BundledAirlineRepository,
    BundledAirportRepository,
)
from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.apollo import ApolloParser
from pnr_convertor.parsing.galileo import GalileoParser
from pnr_convertor.parsing.registry import ParserRegistry
from pnr_convertor.parsing.sabre import SabreParser
from pnr_convertor.parsing.worldspan import WorldspanParser
from pnr_convertor.rendering import HtmlItineraryRenderer, TextItineraryRenderer


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    convert_pnr: ConvertPnr
    renderers: Mapping[RenderFormat, ItineraryRenderer]


def build_parser_registry() -> ParserRegistry:
    return ParserRegistry(
        [AmadeusParser(), SabreParser(), GalileoParser(), WorldspanParser(), ApolloParser()]
    )


def build_renderers() -> dict[RenderFormat, ItineraryRenderer]:
    renderers: list[ItineraryRenderer] = [TextItineraryRenderer(), HtmlItineraryRenderer()]
    return {renderer.format: renderer for renderer in renderers}


def build_container(settings: Settings, *, clock: Clock | None = None) -> Container:
    return Container(
        settings=settings,
        convert_pnr=ConvertPnr(
            build_parser_registry(),
            ItineraryEnricher(BundledAirportRepository(), BundledAirlineRepository()),
            clock or SystemClock(),
        ),
        renderers=build_renderers(),
    )
