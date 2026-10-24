from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Header, Path, Response, status

from pnr_convertor.api.dependencies import AirlineLogosDep
from pnr_convertor.api.errors import problem

router = APIRouter(tags=["airlines"])

# Logos change only when the download script runs again; the ETag catches that.
_CACHE_CONTROL = "public, max-age=604800"
# Served from the API's origin: forbid anything but the image itself.
_SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'",
    "X-Content-Type-Options": "nosniff",
}


@router.get(
    "/airlines/{iata}/logo",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}, 404: {"description": "No logo"}},
)
def airline_logo(
    iata: Annotated[str, Path(pattern=r"^[A-Z0-9]{2}$", description="IATA airline code.")],
    logos: AirlineLogosDep,
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """The airline's logo as a PNG."""
    logo = logos.get(iata)
    if logo is None:
        return problem(
            status_code=status.HTTP_404_NOT_FOUND,
            code="logo_not_found",
            title="Logo not found",
            detail=f"There is no logo for airline {iata}.",
        )
    etag = f'"{hashlib.sha256(logo).hexdigest()[:32]}"'
    headers = {"ETag": etag, "Cache-Control": _CACHE_CONTROL, **_SECURITY_HEADERS}
    if if_none_match == etag:
        return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=headers)
    return Response(logo, media_type="image/png", headers=headers)
