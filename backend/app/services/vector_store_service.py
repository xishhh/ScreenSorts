import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.logging import logger
from app.repository.metadata_repository import MetadataRepository
from app.utils.file_utils import ensure_dir


class VectorStoreService:
    def __init__(self) -> None:
        self.persist_dir = ensure_dir(settings.chroma_persist_path)
        self.collection_name = settings.chroma_collection_name
        self._client: Optional[PersistentClient] = None
        self._collection: Optional[Any] = None

    def _get_client(self) -> PersistentClient:
        if self._client is None:
            logger.info(
                "Initializing ChromaDB persistent client: %s", self.persist_dir
            )
            self._client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self) -> Any:
        if self._collection is None:
            client = self._get_client()
            logger.info(
                "Loading ChromaDB collection: %s", self.collection_name
            )
            try:
                self._collection = client.get_collection(self.collection_name)
            except Exception:
                logger.info(
                    "Creating ChromaDB collection: %s (cosine space)",
                    self.collection_name,
                )
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def _indexed_ids(self) -> set:
        try:
            collection = self._get_collection()
            result = collection.get(include=[])
            return set(result["ids"])
        except Exception:
            return set()

    def has_embedding(self, image_id: str) -> bool:
        return image_id in self._indexed_ids()

    def add_embedding(self, image_id: str) -> bool:
        emb_path = settings.embeddings_path / f"{image_id}.json"
        if not emb_path.exists():
            logger.warning("Embedding file not found: %s", emb_path)
            return False

        emb_data = json.loads(emb_path.read_text(encoding="utf-8"))
        embedding_vec = emb_data["embedding"]

        meta_path = settings.repo_metadata_path / f"{image_id}.json"
        metadata: Dict[str, Any] = {
            "image_id": image_id,
            "image_path": emb_data.get("image_path", ""),
            "embedding_model": emb_data.get("model_name", ""),
        }
        if meta_path.exists():
            meta_data = json.loads(meta_path.read_text(encoding="utf-8"))
            metadata["source_dataset"] = meta_data.get("source_dataset", "")
            metadata["ocr_status"] = meta_data.get("ocr_status", False)
            metadata["created_at"] = meta_data.get("created_at", "")

        collection = self._get_collection()
        collection.add(
            ids=[image_id],
            embeddings=[embedding_vec],
            metadatas=[metadata],
        )

        repo = MetadataRepository(settings.repo_metadata_path)
        repo.update(image_id, indexing_status=True)

        logger.info("Indexed: %s", image_id)
        return True

    def add_batch(self, image_ids: List[str]) -> dict:
        processed = 0
        failed = 0
        skipped = 0
        start_time = time.time()

        for idx, image_id in enumerate(image_ids, 1):
            if self.has_embedding(image_id):
                logger.info("Skipping (already indexed): %s", image_id)
                skipped += 1
                continue

            try:
                if self.add_embedding(image_id):
                    processed += 1
                else:
                    failed += 1
            except Exception:
                logger.exception("Indexing failed: %s", image_id)
                failed += 1

            if idx % 10 == 0:
                logger.info(
                    "Progress: %d/%d indexed", idx, len(image_ids)
                )

        total_time = time.time() - start_time
        avg_time = total_time / len(image_ids) if image_ids else 0

        return {
            "total": len(image_ids),
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "total_time": round(total_time, 2),
            "avg_time_per_image": round(avg_time, 2),
        }

    def index_all(self, batch_size: Optional[int] = None, force: bool = False) -> dict:
        if force:
            self.delete_collection()

        batch_size = batch_size or settings.chroma_batch_size
        embeddings_dir = settings.embeddings_path
        if not embeddings_dir.exists():
            logger.warning("Embeddings directory not found: %s", embeddings_dir)
            return {
                "total": 0, "processed": 0, "failed": 0, "skipped": 0,
                "total_time": 0, "avg_time_per_image": 0,
            }

        emb_files = sorted(embeddings_dir.glob("*.json"))
        if not emb_files:
            logger.warning("No embedding files found in %s", embeddings_dir)
            return {
                "total": 0, "processed": 0, "failed": 0, "skipped": 0,
                "total_time": 0, "avg_time_per_image": 0,
            }

        image_ids = [f.stem for f in emb_files]
        logger.info(
            "Indexing %d embeddings (batch size: %d)",
            len(image_ids), batch_size,
        )

        total_stats = {
            "total": len(image_ids),
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "total_time": 0,
            "avg_time_per_image": 0,
        }

        for start in range(0, len(image_ids), batch_size):
            batch = image_ids[start : start + batch_size]
            stats = self.add_batch(batch)
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

    def collection_stats(self) -> dict:
        try:
            collection = self._get_collection()
            count = collection.count()
            return {
                "exists": True,
                "name": self.collection_name,
                "document_count": count,
                "persist_directory": str(self.persist_dir),
                "embedding_dimension": settings.embedding_dimension,
            }
        except Exception as e:
            return {
                "exists": False,
                "name": self.collection_name,
                "document_count": 0,
                "persist_directory": str(self.persist_dir),
                "error": str(e),
            }

    def health_check(self) -> dict:
        try:
            client = self._get_client()
            client.heartbeat()
            stats = self.collection_stats()
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "document_count": stats["document_count"],
                "persist_directory": str(self.persist_dir),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def query(
        self, query_embeddings: list[list[float]], n_results: int = 10
    ) -> dict:
        collection = self._get_collection()
        return collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            include=["metadatas", "distances"],
        )

    def count(self) -> int:
        try:
            return self._get_collection().count()
        except Exception:
            return 0

    def delete_collection(self) -> None:
        try:
            client = self._get_client()
            client.delete_collection(self.collection_name)
            logger.info("Deleted collection: %s", self.collection_name)
        except Exception:
            logger.info(
                "Collection does not exist (nothing to delete): %s",
                self.collection_name,
            )
        self._collection = None

        repo = MetadataRepository(settings.repo_metadata_path)
        for meta in repo.list_all():
            if meta.indexing_status:
                repo.update(meta.image_id, indexing_status=False)

    def _generate_report(self, stats: dict) -> None:
        report_dir = ensure_dir(settings._resolve("reports"))
        report = {
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_embeddings": stats["total"],
            "indexed": stats["processed"],
            "skipped": stats["skipped"],
            "failed": stats["failed"],
            "collection_name": self.collection_name,
            "storage_path": str(self.persist_dir),
            "total_indexing_time_seconds": stats["total_time"],
            "average_indexing_time_seconds": stats["avg_time_per_image"],
        }
        report_path = report_dir / "index_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Index report written to %s", report_path)
