import argparse
import sys

from app.core.logging import logger
from app.services.ocr_service import OCRService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run OCR pipeline on the demo corpus."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Directory containing screenshots to process (default: data/demo)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of images to process per batch (default: 10)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess images even if OCR results already exist",
    )
    args = parser.parse_args()

    from app.core.config import settings

    if args.dir:
        target_dir = args.dir
    else:
        target_dir = str(settings.repo_demo_path)

    if args.force:
        import shutil

        ocr_dir = settings.ocr_results_path
        if ocr_dir.exists():
            logger.info("Force mode: clearing existing OCR results")
            shutil.rmtree(ocr_dir)
            ocr_dir.mkdir(parents=True, exist_ok=True)
        for meta_path in settings.repo_metadata_path.glob("*.json"):
            from app.repository.metadata_repository import MetadataRepository

            repo = MetadataRepository(settings.repo_metadata_path)
            meta = repo.load(meta_path.stem)
            if meta and meta.ocr_status:
                repo.update(meta.image_id, ocr_status=False, ocr_text_path="")

    from pathlib import Path

    service = OCRService()

    if args.batch_size is not None:
        settings.ocr_batch_size = args.batch_size

    target_path = Path(target_dir)
    if not target_path.is_absolute():
        target_path = settings._resolve(target_dir)

    stats = service.process_directory(target_path, batch_size=args.batch_size)

    logger.info("OCR pipeline complete")
    logger.info("  Total:     %d", stats["total"])
    logger.info("  Processed: %d", stats["processed"])
    logger.info("  Failed:    %d", stats["failed"])
    logger.info("  Skipped:   %d", stats["skipped"])
    logger.info("  Time:      %.2fs", stats["total_time"])


if __name__ == "__main__":
    main()
