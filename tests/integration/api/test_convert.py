from __future__ import annotations

from fastapi.testclient import TestClient

from pnr_convertor.api.v1.schemas import MAX_PNR_LENGTH
from tests.conftest import read_fixture


def test_convert_returns_structured_itinerary(client: TestClient) -> None:
    response = client.post("/v1/convert", json={"pnr": read_fixture("amadeus", "basic_return")})

    assert response.status_code == 200
    body = response.json()
    assert body["gds"] == "amadeus"
    assert body["record_locator"] == "ZX7K2P"
    assert [p["last_name"] for p in body["passengers"]] == ["POPESCU", "POPESCU"]
    assert body["segments"][0]["departure_local"] == "2026-03-15T07:10:00"
    assert body["segments"][0]["status"] == {"code": "HK", "category": "confirmed"}


def test_convert_returns_enrichment(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("amadeus", "connection_via_hub")}
    )

    body = response.json()
    first = body["segments"][0]
    assert first["airline"] == {"iata": "TK", "name": "Turkish Airlines"}
    assert first["origin_airport"]["timezone"] == "Europe/Bucharest"
    assert first["departure_at"] == "2026-04-10T09:05:00+03:00"
    assert first["duration_minutes"] == 105
    outbound = body["journeys"][0]
    assert outbound["segment_indexes"] == [2, 3]
    assert outbound["connections"] == [{"airport": "IST", "duration_minutes": 165}]


def test_unrecognized_format_returns_problem_details(client: TestClient) -> None:
    response = client.post("/v1/convert", json={"pnr": "definitely not a pnr"})

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "unsupported_format"


def test_validation_errors_do_not_echo_input(client: TestClient) -> None:
    oversized = "1.DOE/JANE " * (MAX_PNR_LENGTH // 10)
    response = client.post("/v1/convert", json={"pnr": oversized})

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert "DOE" not in response.text
    assert body["errors"][0]["loc"] == ["body", "pnr"]


def test_unknown_fields_are_rejected(client: TestClient) -> None:
    response = client.post("/v1/convert", json={"pnr": "x", "unexpected": True})
    assert response.status_code == 422
