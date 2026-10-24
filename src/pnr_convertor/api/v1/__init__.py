from fastapi import APIRouter

from pnr_convertor.api.v1 import convert

router = APIRouter(prefix="/v1")
router.include_router(convert.router)
