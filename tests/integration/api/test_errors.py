from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from pnr_convertor.api.errors import register_exception_handlers
from pnr_convertor.domain.errors import PnrParseError


class _Body(BaseModel):
    secret: int


@pytest.fixture
def error_client() -> TestClient:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/fails")
    def fails() -> None:
        raise PnrParseError("nothing usable")

    @app.post("/echo")
    def echo(body: _Body) -> _Body:
        return body

    return TestClient(app)


def test_domain_error_becomes_problem_details(error_client: TestClient) -> None:
    response = error_client.get("/fails")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank#parse_error",
        "title": "PNR could not be converted",
        "status": 422,
        "code": "parse_error",
        "detail": "nothing usable",
    }


def test_validation_error_hides_input(error_client: TestClient) -> None:
    response = error_client.post("/echo", json={"secret": "DOE/JANE"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert "DOE/JANE" not in response.text
