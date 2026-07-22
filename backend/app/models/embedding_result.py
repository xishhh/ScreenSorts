from datetime import datetime, timezone

from pydantic import BaseModel, Field


class EmbeddingResult(BaseModel):
    image_id: str
    image_path: str
    embedding: list[float]
    model_name: str
    dimension: int
    full_text: str
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
