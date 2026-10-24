from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_serves_a_logo_with_cache_and_security_headers(client: TestClient) -> None:
    response = client.get("/v1/airlines/TK/logo")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(PNG_SIGNATURE)
    assert response.headers["cache-control"] == "public, max-age=604800"
    assert response.headers["content-security-policy"] == "default-src 'none'"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_unchanged_logo_is_not_sent_again(client: TestClient) -> None:
    etag = client.get("/v1/airlines/TK/logo").headers["etag"]

    response = client.get("/v1/airlines/TK/logo", headers={"If-None-Match": etag})

    assert response.status_code == 304
    assert response.content == b""


def test_missing_logo_is_a_problem(client: TestClient) -> None:
    response = client.get("/v1/airlines/ZZ/logo")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["code"] == "logo_not_found"


@pytest.mark.parametrize("code", ["tk", "TKX", "..", "T%2F"])
def test_invalid_code_is_rejected(client: TestClient, code: str) -> None:
    assert client.get(f"/v1/airlines/{code}/logo").status_code in (404, 422)
