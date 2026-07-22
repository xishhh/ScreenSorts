from pydantic import BaseModel, Field


class ExplainRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query to explain results for")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to retrieve and explain")
    threshold: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    image_ids: list[str] | None = Field(default=None, description="Specific image IDs to explain. If provided, top_k/threshold are ignored and only these are explained.")


class ExplainItem(BaseModel):
    image_id: str
    image_path: str = ""
    text: str = ""
    score: float = 0.0
    source_dataset: str = ""
    explanation: str = ""
    model: str = ""
    cache_hit: bool = False
    latency_ms: float = 0.0


class ExplainTiming(BaseModel):
    search_ms: float = 0.0
    explain_ms: float = 0.0
    total_ms: float = 0.0


class ExplainResponse(BaseModel):
    query: str
    top_k: int
    threshold: float
    total_explanations: int
    explanations: list[ExplainItem]
    timing: ExplainTiming
