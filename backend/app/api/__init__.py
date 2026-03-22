from fastapi import APIRouter

from backend.app.api.health import router as health_router
from backend.app.api.strategies import router as strategies_router


router = APIRouter()
router.include_router(health_router)
router.include_router(strategies_router)
