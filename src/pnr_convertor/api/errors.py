"""RFC 9457 problem details."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from pnr_convertor.domain.errors import PnrConvertorError

PROBLEM_JSON = "application/problem+json"


def problem(*, status_code: int, code: str, title: str, detail: str, **extra: Any) -> JSONResponse:
    body = {
        "type": f"about:blank#{code}",
        "title": title,
        "status": status_code,
        "code": code,
        "detail": detail,
        **extra,
    }
    return JSONResponse(jsonable_encoder(body), status_code=status_code, media_type=PROBLEM_JSON)


async def _domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, PnrConvertorError)  # noqa: S101
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code=exc.code,
        title="PNR could not be converted",
        detail=exc.message,
    )


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101
    # `input` would echo PNR text, which contains personal data.
    errors = [{k: v for k, v in err.items() if k != "input"} for err in exc.errors()]
    return problem(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="validation_error",
        title="Invalid request",
        detail="The request body failed validation",
        errors=errors,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PnrConvertorError, _domain_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
