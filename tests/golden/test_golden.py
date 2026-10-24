"""Golden tests: every `fixtures/pnr/<gds>/<name>.txt` must convert to `<name>.expected.json`.

To add a case, drop a new `.txt` fixture and run `make golden`, then review the generated JSON
by hand before committing. A golden file is only as correct as the review it received.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from pnr_convertor.api.v1.schemas import ConvertResponse
from pnr_convertor.application.convert_pnr import ConvertPnrCommand
from pnr_convertor.bootstrap import Container
from tests.conftest import FIXTURES_DIR

UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"
CASES = sorted(FIXTURES_DIR.glob("*/*.txt"))


@pytest.mark.parametrize("fixture", CASES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_golden(fixture: Path, container: Container) -> None:
    itinerary = container.convert_pnr.execute(ConvertPnrCommand(text=fixture.read_text()))
    actual = ConvertResponse.from_domain(itinerary).model_dump(mode="json")

    expected_path = fixture.with_suffix(".expected.json")
    if UPDATE:
        expected_path.write_text(json.dumps(actual, indent=2) + "\n")

    assert expected_path.exists(), f"Missing {expected_path.name}; run `make golden`"
    assert actual == json.loads(expected_path.read_text())
