from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, Response

from pnr_convertor.api.dependencies import ConvertPnrDep, RenderersDep
from pnr_convertor.api.v1.schemas import ConvertRequest, ConvertResponse, OutputFormat
from pnr_convertor.application.convert_pnr import ConvertPnrCommand
from pnr_convertor.application.ports import RenderFormat

router = APIRouter(tags=["convert"])


@router.post(
    "/convert",
    response_model=ConvertResponse,
    responses={
        200: {
            "content": {"text/plain": {}, "text/html": {}},
            "description": "The itinerary as JSON, plain text or HTML, per `format`.",
        }
    },
)
def convert(
    body: ConvertRequest,
    convert_pnr: ConvertPnrDep,
    renderers: RenderersDep,
    output: Annotated[
        OutputFormat,
        Query(
            alias="format", description="`json` (default), or a readable `text` / `html` itinerary."
        ),
    ] = OutputFormat.JSON,
) -> ConvertResponse | Response:
    """Convert raw GDS PNR text into a structured itinerary."""
    itinerary = convert_pnr.execute(
        ConvertPnrCommand(text=body.pnr, gds=body.gds, reference_date=body.reference_date)
    )
    if output is OutputFormat.JSON:
        return ConvertResponse.from_domain(itinerary)
    renderer = renderers[RenderFormat(output.value)]
    return Response(renderer.render(itinerary), media_type=renderer.media_type)
