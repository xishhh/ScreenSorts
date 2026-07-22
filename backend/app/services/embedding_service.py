import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.models.embedding_result import EmbeddingResult
from app.models.screenshot_metadata import ScreenshotMetadata
from app.repository.metadata_repository import MetadataRepository
from app.utils.file_utils import ensure_dir


class EmbeddingService:
    def __init__(self) -> None:
        self.embeddings_dir = ensure_dir(settings.embeddings_path)
        self.metadata_repo = MetadataRepository(settings.repo_metadata_path)
        self._model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(
                "Loading embedding model: %s", settings.embedding_model_name
            )
            self._model = SentenceTransformer(settings.embedding_model_name)
        return self._model

    def _embedding_path(self, image_id: str) -> Path:
        return self.embeddings_dir / f"{image_id}.json"

    def has_embedding(self, image_id: str) -> bool:
        return self._embedding_path(image_id).exists()

    @staticmethod
    def prepare_text(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def process_document(self, image_id: str) -> EmbeddingResult:
        ocr_path = settings.ocr_results_path / f"{image_id}.json"
        if not ocr_path.exists():
            raise FileNotFoundError(f"OCR result not found for {image_id}")

        ocr_data = json.loads(ocr_path.read_text(encoding="utf-8"))
        raw_text = ocr_data.get("full_text", "")
        cleaned_text = self.prepare_text(raw_text)

        if not cleaned_text:
            logger.warning("Empty text for %s — generating zero embedding", image_id)
            dimension = settings.embedding_dimension
            embedding_vec = np.zeros(dimension, dtype=np.float32).tolist()
        else:
            model = self._get_model()
            embedding_vec = model.encode(
                cleaned_text, normalize_embeddings=True
            ).tolist()

        result = EmbeddingResult(
            image_id=image_id,
            image_path=ocr_data.get("image_path", ""),
            embedding=embedding_vec,
            model_name=settings.embedding_model_name,
            dimension=settings.embedding_dimension,
            full_text=cleaned_text,
        )

        result_path = self._embedding_path(image_id)
        result_path.write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )

        self.metadata_repo.update(
            image_id,
            embedding_status=True,
            embedding_path=str(result_path),
            embedding_model=settings.embedding_model_name,
        )

        logger.info(
            "Embedding complete: %s — dim: %d, text: %d chars",
            image_id, settings.embedding_dimension, len(cleaned_text),
        )

        return result

    def process_batch(self, image_ids: List[str]) -> dict:
        results = []
        failed = 0
        skipped = 0
        start_time = time.time()

        for idx, image_id in enumerate(image_ids, 1):
            if self.has_embedding(image_id):
                logger.info("Skipping (already embedded): %s", image_id)
                skipped += 1
                continue

            try:
                result = self.process_document(image_id)
                results.append(result)
            except Exception:
                logger.exception("Embedding failed: %s", image_id)
                failed += 1

            if idx % 5 == 0:
                logger.info(
                    "Progress: %d/%d embeddings processed", idx, len(image_ids)
                )

        total_time = time.time() - start_time
        avg_time = total_time / len(image_ids) if image_ids else 0

        return {
            "total": len(image_ids),
            "processed": len(results),
            "failed": failed,
            "skipped": skipped,
            "total_time": round(total_time, 2),
            "avg_time_per_image": round(avg_time, 2),
        }

    def process_all(
        self, batch_size: Optional[int] = None
    ) -> dict:
        batch_size = batch_size or settings.embedding_batch_size
        all_metadata = self.metadata_repo.list_all()

        ocr_completed = [
            m for m in all_metadata if m.ocr_status
        ]

        if not ocr_completed:
            logger.warning("No OCR-completed screenshots found")
            return {
                "total": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "total_time": 0,
                "avg_time_per_image": 0,
            }

        logger.info(
            "Processing %d OCR-completed screenshots (batch size: %d)",
            len(ocr_completed), batch_size,
        )

        total_stats = {
            "total": len(ocr_completed),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0,
            "avg_time_per_image": 0,
        }

        image_ids = [m.image_id for m in ocr_completed]

        for start in range(0, len(image_ids), batch_size):
            batch = image_ids[start : start + batch_size]
            stats = self.process_batch(batch)
            total_stats["processed"] += stats["processed"]
            total_stats["failed"] += stats["failed"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["total_time"] += stats["total_time"]

        total_stats["avg_time_per_image"] = round(
            total_stats["total_time"] / total_stats["total"], 2
        ) if total_stats["total"] else 0

        total_stats["total_time"] = round(total_stats["total_time"], 2)

        self._generate_report(total_stats)

        return total_stats

    def _generate_report(self, stats: dict) -> None:
        report_dir = ensure_dir(settings._resolve("reports"))
        report = {
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "images_total": stats["total"],
            "successful_embeddings": stats["processed"],
            "failed_embeddings": stats["failed"],
            "skipped": stats["skipped"],
            "average_processing_time_seconds": stats["avg_time_per_image"],
            "total_processing_time_seconds": stats["total_time"],
            "embedding_model": settings.embedding_model_name,
            "embedding_dimension": settings.embedding_dimension,
        }
        report_path = report_dir / "embedding_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Embedding report written to %s", report_path)
