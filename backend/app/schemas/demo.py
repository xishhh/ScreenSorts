from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DemoComponentStatus(BaseModel):
    name: str
    exists: bool
    count: int = 0
    details: str = ""


class DemoStatusResponse(BaseModel):
    ready: bool
    screenshot_count: int
    dataset_count: int
    datasets: list[str]
    total_storage_bytes: int
    build_timestamp: Optional[str] = None
    ocr: DemoComponentStatus
    embeddings: DemoComponentStatus
    index: DemoComponentStatus
    corpus: DemoComponentStatus
