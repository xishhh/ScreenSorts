import hashlib
import json
from pathlib import Path

from app.core.config import settings
from app.core.logging import logger
from app.utils.file_utils import ensure_dir


class ExplanationCache:
    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = ensure_dir(cache_dir or settings._resolve(settings.groq_cache_dir))

    def _make_key(self, query: str, image_id: str, model: str) -> str:
        raw = f"{query}||{image_id}||{model}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, query: str, image_id: str, model: str) -> str | None:
        key = self._make_key(query, image_id, model)
        path = self._cache_path(key)
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                logger.debug("Cache HIT for query=%s image=%s", query[:50], image_id)
                return data.get("explanation")
            except Exception:
                pass
        logger.debug("Cache MISS for query=%s image=%s", query[:50], image_id)
        return None

    def set(
        self, query: str, image_id: str, model: str, explanation: str
    ) -> None:
        key = self._make_key(query, image_id, model)
        path = self._cache_path(key)
        data = {
            "query": query,
            "image_id": image_id,
            "model": model,
            "key": key,
            "explanation": explanation,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def clear(self) -> int:
        count = 0
        for p in self.cache_dir.glob("*.json"):
            p.unlink()
            count += 1
        logger.info("Cleared %d cache entries from %s", count, self.cache_dir)
        return count

    @property
    def size(self) -> int:
        return sum(1 for _ in self.cache_dir.glob("*.json"))
