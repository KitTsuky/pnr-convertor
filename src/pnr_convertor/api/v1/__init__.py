from fastapi import APIRouter

from pnr_convertor.api.v1 import airlines, convert

router = APIRouter(prefix="/v1")
router.include_router(convert.router)
router.include_router(airlines.router)
