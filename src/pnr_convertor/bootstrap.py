"""Composition root: the only place concrete implementations are wired together."""

from __future__ import annotations

from dataclasses import dataclass

from pnr_convertor.application.convert_pnr import ConvertPnr
from pnr_convertor.application.ports import Clock
from pnr_convertor.config import Settings
from pnr_convertor.infrastructure.clock import SystemClock
from pnr_convertor.parsing.amadeus import AmadeusParser
from pnr_convertor.parsing.registry import ParserRegistry


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    convert_pnr: ConvertPnr


def build_parser_registry() -> ParserRegistry:
    return ParserRegistry([AmadeusParser()])


def build_container(settings: Settings, *, clock: Clock | None = None) -> Container:
    return Container(
        settings=settings,
        convert_pnr=ConvertPnr(build_parser_registry(), clock or SystemClock()),
    )
