from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from pnr_convertor.domain.models import GdsFormat, ParsedPnr


@dataclass(frozen=True, slots=True)
class ParseContext:
    """`reference_date` anchors year inference, since GDS dates like `15MAR` have no year."""

    reference_date: date


class PnrParser(Protocol):
    """Stateless parser for one GDS format. Receives text already normalized."""

    @property
    def gds(self) -> GdsFormat: ...

    def detect(self, text: str) -> float:
        """Confidence in [0, 1] that `text` is in this format."""
        ...

    def parse(self, text: str, context: ParseContext) -> ParsedPnr: ...
