import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.screenshot_metadata import ScreenshotMetadata
from app.utils.file_utils import ensure_dir


class MetadataRepository:
    def __init__(self, storage_dir: Path):
        self.storage_dir = ensure_dir(storage_dir)

    def _file_path(self, image_id: str) -> Path:
        return self.storage_dir / f"{image_id}.json"

    def create(self, metadata: ScreenshotMetadata) -> ScreenshotMetadata:
        path = self._file_path(metadata.image_id)
        if path.exists():
            raise FileExistsError(f"Metadata already exists for {metadata.image_id}")
        self.save(metadata)
        return metadata

    def save(self, metadata: ScreenshotMetadata) -> ScreenshotMetadata:
        path = self._file_path(metadata.image_id)
        metadata.updated_at = datetime.now(timezone.utc)
        path.write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
        return metadata

    def load(self, image_id: str) -> Optional[ScreenshotMetadata]:
        path = self._file_path(image_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return ScreenshotMetadata(**data)

    def update(
        self, image_id: str, **kwargs
    ) -> Optional[ScreenshotMetadata]:
        metadata = self.load(image_id)
        if metadata is None:
            return None
        for key, value in kwargs.items():
            if hasattr(metadata, key):
                setattr(metadata, key, value)
        return self.save(metadata)

    def delete(self, image_id: str) -> bool:
        path = self._file_path(image_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def list_all(self) -> list[ScreenshotMetadata]:
        metadata_list: list[ScreenshotMetadata] = []
        for path in self.storage_dir.glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            metadata_list.append(ScreenshotMetadata(**data))
        return metadata_list

    def count(self) -> int:
        return len(list(self.storage_dir.glob("*.json")))
