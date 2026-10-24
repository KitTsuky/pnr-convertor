"""Application factory. Run with: `uvicorn --factory pnr_convertor.main:create_app`."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from pnr_convertor import __version__
from pnr_convertor.api import health, v1
from pnr_convertor.api.errors import register_exception_handlers
from pnr_convertor.bootstrap import Container, build_container
from pnr_convertor.config import Settings


def create_app(settings: Settings | None = None, *, container: Container | None = None) -> FastAPI:
    settings = settings or Settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(
        title="PNR Convertor API",
        version=__version__,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )
    app.state.container = container or build_container(settings)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(v1.router)
    return app
