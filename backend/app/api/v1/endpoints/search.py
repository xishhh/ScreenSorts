from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter()
_service: SearchService | None = None


def _get_service() -> SearchService:
    global _service
    if _service is None:
        _service = SearchService()
    return _service


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    return _get_service().search(request)
