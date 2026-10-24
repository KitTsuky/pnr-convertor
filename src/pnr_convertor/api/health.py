from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from pnr_convertor import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = __version__


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse()
