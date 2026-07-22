import argparse
import sys

from app.core.logging import logger
from app.services.embedding_service import EmbeddingService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate embeddings from OCR results."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of documents to process per batch (default: 32)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate embeddings even if they already exist",
    )
    args = parser.parse_args()

    from app.core.config import settings

    if args.force:
        import shutil

        emb_dir = settings.embeddings_path
        if emb_dir.exists():
            logger.info("Force mode: clearing existing embeddings")
            shutil.rmtree(emb_dir)
            emb_dir.mkdir(parents=True, exist_ok=True)
        for meta_path in settings.repo_metadata_path.glob("*.json"):
            from app.repository.metadata_repository import MetadataRepository

            repo = MetadataRepository(settings.repo_metadata_path)
            meta = repo.load(meta_path.stem)
            if meta and meta.embedding_status:
                repo.update(
                    meta.image_id,
                    embedding_status=False,
                    embedding_path="",
                    embedding_model="",
                )

    service = EmbeddingService()

    if args.batch_size is not None:
        settings.embedding_batch_size = args.batch_size

    stats = service.process_all(batch_size=args.batch_size)

    logger.info("Embedding pipeline complete")
    logger.info("  Total:     %d", stats["total"])
    logger.info("  Processed: %d", stats["processed"])
    logger.info("  Failed:    %d", stats["failed"])
    logger.info("  Skipped:   %d", stats["skipped"])
    logger.info("  Time:      %.2fs", stats["total_time"])


if __name__ == "__main__":
    main()
