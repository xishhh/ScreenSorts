import argparse
import sys

from app.core.logging import logger
from app.services.vector_store_service import VectorStoreService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index embeddings into ChromaDB."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Number of embeddings to index per batch (default: 50)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing collection and re-index all embeddings",
    )
    args = parser.parse_args()

    from app.core.config import settings

    if args.batch_size is not None:
        settings.chroma_batch_size = args.batch_size

    service = VectorStoreService()
    stats = service.index_all(batch_size=args.batch_size, force=args.force)

    logger.info("Indexing pipeline complete")
    logger.info("  Total:    %d", stats["total"])
    logger.info("  Indexed:  %d", stats["processed"])
    logger.info("  Failed:   %d", stats["failed"])
    logger.info("  Skipped:  %d", stats["skipped"])
    logger.info("  Time:     %.2fs", stats["total_time"])


if __name__ == "__main__":
    main()
