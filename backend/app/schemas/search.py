from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SearchResultItem(BaseModel):
    image_id: str
    image_path: str
    text: str = ""
    score: float
    source_dataset: str = ""
    ocr_status: bool = False
    embedding_model: str = ""
    created_at: str = ""


class SearchTiming(BaseModel):
    query_embedding_ms: float
    vector_search_ms: float
    total_ms: float


class SearchResponse(BaseModel):
    query: str
    top_k: int
    threshold: float
    results: list[SearchResultItem]
    total_results: int
    timing: SearchTiming
