from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from fastapi import Depends, Request

from pnr_convertor.application.convert_pnr import ConvertPnr
from pnr_convertor.application.ports import AirlineLogoRepository, ItineraryRenderer, RenderFormat
from pnr_convertor.bootstrap import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_convert_pnr(container: Annotated[Container, Depends(get_container)]) -> ConvertPnr:
    return container.convert_pnr


ConvertPnrDep = Annotated[ConvertPnr, Depends(get_convert_pnr)]


def get_renderers(
    container: Annotated[Container, Depends(get_container)],
) -> Mapping[RenderFormat, ItineraryRenderer]:
    return container.renderers


RenderersDep = Annotated[Mapping[RenderFormat, ItineraryRenderer], Depends(get_renderers)]


def get_airline_logos(
    container: Annotated[Container, Depends(get_container)],
) -> AirlineLogoRepository:
    return container.airline_logos


AirlineLogosDep = Annotated[AirlineLogoRepository, Depends(get_airline_logos)]
