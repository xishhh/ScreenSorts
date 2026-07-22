from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ScreenshotMetadata(BaseModel):
    image_id: str
    image_path: str
    source_dataset: str = ""
    ocr_status: bool = False
    embedding_status: bool = False
    indexing_status: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
