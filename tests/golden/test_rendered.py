"""Golden tests for readable itineraries: every PNR fixture renders to `rendered/<gds>/<name>.txt`,
and a few to `.html`. Regenerate with `make golden` and read the diff as a traveller would.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pnr_convertor.application.convert_pnr import ConvertPnrCommand
from pnr_convertor.application.ports import RenderFormat
from pnr_convertor.bootstrap import Container
from tests.conftest import FIXTURES_DIR

UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"
RENDERED_DIR = FIXTURES_DIR.parent / "rendered"
CASES = sorted(FIXTURES_DIR.glob("*/*.txt"))
HTML_CASES = [
    FIXTURES_DIR / "amadeus" / "ticketed_with_seats_and_contacts.txt",
    FIXTURES_DIR / "apollo" / "overnight_codeshare_connection.txt",
    FIXTURES_DIR / "sabre" / "ticketed_family_full_display.txt",
]


def _check(fixture: Path, render_format: RenderFormat, container: Container) -> None:
    itinerary = container.convert_pnr.execute(ConvertPnrCommand(text=fixture.read_text()))
    actual = container.renderers[render_format].render(itinerary)

    suffix = ".txt" if render_format is RenderFormat.TEXT else ".html"
    expected_path = RENDERED_DIR / fixture.parent.name / f"{fixture.stem}{suffix}"
    if UPDATE:
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        expected_path.write_text(actual)

    assert expected_path.exists(), f"Missing {expected_path.name}; run `make golden`"
    assert actual == expected_path.read_text()


@pytest.mark.parametrize("fixture", CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_rendered_text(fixture: Path, container: Container) -> None:
    _check(fixture, RenderFormat.TEXT, container)


@pytest.mark.parametrize("fixture", HTML_CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_rendered_html(fixture: Path, container: Container) -> None:
    _check(fixture, RenderFormat.HTML, container)
