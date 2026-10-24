from __future__ import annotations

from collections.abc import Iterable

from pnr_convertor.domain.errors import UnsupportedFormatError
from pnr_convertor.domain.models import GdsFormat
from pnr_convertor.parsing.base import PnrParser

MIN_DETECTION_CONFIDENCE = 0.5


class ParserRegistry:
    def __init__(self, parsers: Iterable[PnrParser]) -> None:
        self._parsers: dict[GdsFormat, PnrParser] = {}
        for parser in parsers:
            if parser.gds in self._parsers:
                raise ValueError(f"Duplicate parser registered for {parser.gds}")
            self._parsers[parser.gds] = parser

    @property
    def supported_formats(self) -> tuple[GdsFormat, ...]:
        return tuple(self._parsers)

    def resolve(self, text: str, gds: GdsFormat | None = None) -> PnrParser:
        if gds is not None:
            parser = self._parsers.get(gds)
            if parser is None:
                raise UnsupportedFormatError(f"No parser available for format '{gds}'")
            return parser

        scored = [(parser.detect(text), parser) for parser in self._parsers.values()]
        confidence, best = max(scored, key=lambda item: item[0], default=(0.0, None))
        if best is None or confidence < MIN_DETECTION_CONFIDENCE:
            raise UnsupportedFormatError(
                "Could not recognize the PNR format. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )
        return best
