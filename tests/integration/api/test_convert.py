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
    assert body["segments"][0]["status"] == {
        "code": "HK",
        "category": "confirmed",
        "description": "Holding confirmed",
    }


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


def test_convert_auto_detects_sabre(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("sabre", "round_trip_with_fare_quote")}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["gds"] == "sabre"
    assert [s["flight_number"] for s in body["segments"]] == ["142", "101"]


def test_convert_returns_tickets_seats_and_contacts(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("amadeus", "ticketed_with_seats_and_contacts")}
    )

    body = response.json()
    assert body["segments"][0]["seats"] == [
        {"passenger_index": 1, "seat": "12A"},
        {"passenger_index": 2, "seat": "12B"},
    ]
    assert [t["number"] for t in body["tickets"]] == ["125-9876543210", "125-9876543211"]
    assert {c["kind"] for c in body["contacts"]} == {"phone", "email"}


def test_convert_returns_distances(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("sabre", "verify_itinerary_and_display")}
    )

    body = response.json()
    assert body["segments"][0]["distance"] == {"km": 5555, "miles": 3451}
    assert body["journeys"][0]["distance"] == {"km": 5555, "miles": 3451}


def test_convert_returns_passenger_types_and_infants(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("amadeus", "children_and_infants")}
    )

    passengers = response.json()["passengers"]
    assert [p["type"] for p in passengers] == ["ADT", "CHD", "ADT", "INS"]
    assert passengers[0]["infant"] == {
        "last_name": "POPESCU",
        "first_name": "ILINCA",
        "date_of_birth": "2024-01-14",
    }


def test_convert_auto_detects_galileo(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("galileo", "booking_file_connections")}
    )

    body = response.json()
    assert (body["gds"], body["record_locator"]) == ("galileo", "K7PL2Q")
    assert [j["segment_indexes"] for j in body["journeys"]] == [[1, 2], [3, 4]]


def test_convert_auto_detects_worldspan(client: TestClient) -> None:
    response = client.post(
        "/v1/convert", json={"pnr": read_fixture("worldspan", "ticketed_overnight_connections")}
    )

    body = response.json()
    assert (body["gds"], body["record_locator"]) == ("worldspan", "7KQ2ZX")
    assert body["segments"][2]["arrival_local"] == "2025-12-13T07:45:00"
    assert body["tickets"][0]["number"] == "281-1234567890"
