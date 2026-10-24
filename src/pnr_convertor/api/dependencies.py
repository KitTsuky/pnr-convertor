from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from pnr_convertor.application.convert_pnr import ConvertPnr
from pnr_convertor.bootstrap import Container


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


def get_convert_pnr(container: Annotated[Container, Depends(get_container)]) -> ConvertPnr:
    return container.convert_pnr


ConvertPnrDep = Annotated[ConvertPnr, Depends(get_convert_pnr)]
