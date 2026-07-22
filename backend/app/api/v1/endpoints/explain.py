from fastapi import APIRouter

from app.schemas.explain import ExplainRequest, ExplainResponse
from app.services.explanation_service import ExplanationService

router = APIRouter()
_service: ExplanationService | None = None


def _get_service() -> ExplanationService:
    global _service
    if _service is None:
        _service = ExplanationService()
    return _service


@router.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest) -> ExplainResponse:
    return _get_service().explain(request)
