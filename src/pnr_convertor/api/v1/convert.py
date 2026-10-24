from __future__ import annotations

from fastapi import APIRouter

from pnr_convertor.api.dependencies import ConvertPnrDep
from pnr_convertor.api.v1.schemas import ConvertRequest, ConvertResponse
from pnr_convertor.application.convert_pnr import ConvertPnrCommand

router = APIRouter(tags=["convert"])


@router.post("/convert")
def convert(body: ConvertRequest, convert_pnr: ConvertPnrDep) -> ConvertResponse:
    """Convert raw GDS PNR text into a structured itinerary."""
    itinerary = convert_pnr.execute(
        ConvertPnrCommand(text=body.pnr, gds=body.gds, reference_date=body.reference_date)
    )
    return ConvertResponse.from_domain(itinerary)
