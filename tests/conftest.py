from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pnr_convertor.bootstrap import build_container
from pnr_convertor.config import Settings
from pnr_convertor.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pnr"

# Every test runs "as if today were" this date, so year inference is deterministic.
REFERENCE_DATE = date(2026, 1, 15)


@dataclass(frozen=True)
class FixedClock:
    value: date = REFERENCE_DATE

    def today(self) -> date:
        return self.value


def read_fixture(gds: str, name: str) -> str:
    return (FIXTURES_DIR / gds / f"{name}.txt").read_text()


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test")


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    app = create_app(settings, container=build_container(settings, clock=FixedClock()))
    with TestClient(app) as test_client:
        yield test_client
