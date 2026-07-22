from datetime import datetime, timezone

from pydantic import BaseModel, Field


class OCRResult(BaseModel):
    image_id: str
    image_path: str
    texts: list[str]
    confidences: list[float]
    full_text: str
    avg_confidence: float
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
