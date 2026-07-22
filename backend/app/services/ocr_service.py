import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from paddleocr import PaddleOCR

from app.core.config import settings
from app.core.logging import logger
from app.models.ocr_result import OCRResult
from app.models.screenshot_metadata import ScreenshotMetadata
from app.repository.metadata_repository import MetadataRepository
from app.utils.file_utils import ensure_dir, image_files


class OCRService:
    def __init__(self) -> None:
        self.ocr_results_dir = ensure_dir(settings.ocr_results_path)
        self.metadata_repo = MetadataRepository(settings.repo_metadata_path)
        self._ocr: Optional[PaddleOCR] = None

    def _get_ocr(self) -> PaddleOCR:
        if self._ocr is None:
            logger.info("Initializing PaddleOCR (CPU, English)")
            self._ocr = PaddleOCR(use_angle_cls=False, lang="en")
        return self._ocr

    def _ocr_result_path(self, image_id: str) -> Path:
        return self.ocr_results_dir / f"{image_id}.json"

    def has_ocr_result(self, image_id: str) -> bool:
        return self._ocr_result_path(image_id).exists()

    def process_image(self, image_path: Path) -> OCRResult:
        image_path = Path(image_path)
        image_id = image_path.stem
        logger.info("Processing: %s", image_path.name)

        ocr = self._get_ocr()
        result = ocr.ocr(str(image_path), cls=False)

        texts: list[str] = []
        confidences: list[float] = []

        if result and result[0]:
            for line in result[0]:
                bbox, (text, confidence) = line
                texts.append(text)
                confidences.append(confidence)

        full_text = " ".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        ocr_result = OCRResult(
            image_id=image_id,
            image_path=str(image_path),
            texts=texts,
            confidences=confidences,
            full_text=full_text,
            avg_confidence=avg_confidence,
        )

        result_path = self._ocr_result_path(image_id)
        result_path.write_text(
            ocr_result.model_dump_json(indent=2), encoding="utf-8"
        )

        self.metadata_repo.update(
            image_id,
            ocr_status=True,
            ocr_text_path=str(result_path),
        )

        logger.info(
            "OCR complete: %s — %d text(s), avg confidence: %.2f",
            image_path.name, len(texts), avg_confidence,
        )

        return ocr_result

    def process_batch(self, image_paths: List[Path]) -> dict:
        results = []
        failed = 0
        skipped = 0
        start_time = time.time()

        for idx, image_path in enumerate(image_paths, 1):
            image_id = image_path.stem

            if self.has_ocr_result(image_id):
                logger.info("Skipping (already processed): %s", image_path.name)
                skipped += 1
                continue

            try:
                ocr_result = self.process_image(image_path)
                results.append(ocr_result)
            except Exception:
                logger.exception("OCR failed: %s", image_path.name)
                failed += 1

            if idx % 5 == 0:
                logger.info("Progress: %d/%d images processed", idx, len(image_paths))

        total_time = time.time() - start_time
        avg_time = total_time / len(image_paths) if image_paths else 0

        return {
            "total": len(image_paths),
            "processed": len(results),
            "failed": failed,
            "skipped": skipped,
            "total_time": round(total_time, 2),
            "avg_time_per_image": round(avg_time, 2),
        }

    def process_directory(
        self, directory: Path, batch_size: Optional[int] = None
    ) -> dict:
        directory = Path(directory)
        batch_size = batch_size or settings.ocr_batch_size
        images = image_files(directory)

        if not images:
            logger.warning("No images found in %s", directory)
            return {
                "total": 0,
                "processed": 0,
                "failed": 0,
                "skipped": 0,
                "total_time": 0,
                "avg_time_per_image": 0,
            }

        logger.info(
            "Processing directory: %s (%d images, batch size: %d)",
            directory, len(images), batch_size,
        )

        total_stats = {
            "total": len(images),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0,
            "avg_time_per_image": 0,
        }

        for start in range(0, len(images), batch_size):
            batch = images[start : start + batch_size]
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
            "successful_ocr": stats["processed"],
            "failed_ocr": stats["failed"],
            "skipped": stats["skipped"],
            "average_processing_time_seconds": stats["avg_time_per_image"],
            "total_processing_time_seconds": stats["total_time"],
        }
        report_path = report_dir / "ocr_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("OCR report written to %s", report_path)
