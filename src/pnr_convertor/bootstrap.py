"""Composition root: the only place concrete implementations are wired together."""

from __future__ import annotations

from dataclasses import dataclass

from pnr_convertor.config import Settings


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings


def build_container(settings: Settings) -> Container:
    return Container(settings=settings)
