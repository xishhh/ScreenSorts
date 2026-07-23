from fastapi import APIRouter

from app.schemas.demo import DemoStatusResponse
from app.services.demo_mode_service import DemoModeService

router = APIRouter()
_service = DemoModeService()


@router.get("/demo/status", response_model=DemoStatusResponse)
async def demo_status() -> DemoStatusResponse:
    return _service.check_readiness()
