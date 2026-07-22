import json
import time
from datetime import datetime, timezone
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger
from app.schemas.search import (
    SearchRequest,
    SearchResultItem,
    SearchResponse,
    SearchTiming,
)
from app.services.vector_store_service import VectorStoreService
from app.utils.file_utils import ensure_dir


class SearchService:
    def __init__(self) -> None:
        self.vector_store = VectorStoreService()
        self._model: Optional[SentenceTransformer] = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info(
                "Loading embedding model for search: %s",
                settings.embedding_model_name,
            )
            self._model = SentenceTransformer(settings.embedding_model_name)
        return self._model

    def preprocess_query(self, query: str) -> str:
        return query.strip()

    def generate_query_embedding(self, query: str) -> list[float]:
        model = self._get_model()
        embedding = model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def search(self, request: SearchRequest) -> SearchResponse:
        query = self.preprocess_query(request.query)
        if not query:
            return SearchResponse(
                query=request.query,
                top_k=request.top_k,
                threshold=request.threshold,
                results=[],
                total_results=0,
                timing=SearchTiming(
                    query_embedding_ms=0,
                    vector_search_ms=0,
                    total_ms=0,
                ),
            )

        total_start = time.time()
        emb_start = time.time()
        query_emb = self.generate_query_embedding(query)
        emb_time = (time.time() - emb_start) * 1000

        search_start = time.time()
        results = self._query_chromadb(query_emb, request.top_k, request.threshold)
        search_time = (time.time() - search_start) * 1000

        total_time = (time.time() - total_start) * 1000

        response = SearchResponse(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            results=results,
            total_results=len(results),
            timing=SearchTiming(
                query_embedding_ms=round(emb_time, 2),
                vector_search_ms=round(search_time, 2),
                total_ms=round(total_time, 2),
            ),
        )

        self._generate_report(response)
        return response

    def _query_chromadb(
        self, query_emb: list[float], top_k: int, threshold: float
    ) -> List[SearchResultItem]:
        count = self.vector_store.count()
        if count == 0:
            return []

        n_results = min(top_k, count)
        raw = self.vector_store.query(
            query_embeddings=[query_emb], n_results=n_results
        )

        if not raw["ids"] or not raw["ids"][0]:
            return []

        items: List[SearchResultItem] = []
        for i in range(len(raw["ids"][0])):
            distance = raw["distances"][0][i]
            similarity = max(0.0, 1.0 - distance)

            if similarity < threshold:
                continue

            meta = raw["metadatas"][0][i] if raw["metadatas"] else {}

            text = self._get_ocr_text(raw["ids"][0][i])

            items.append(
                SearchResultItem(
                    image_id=raw["ids"][0][i],
                    image_path=meta.get("image_path", ""),
                    text=text,
                    score=round(similarity, 4),
                    source_dataset=meta.get("source_dataset", ""),
                    ocr_status=meta.get("ocr_status", False),
                    embedding_model=meta.get("embedding_model", ""),
                    created_at=meta.get("created_at", ""),
                )
            )

        return items

    @staticmethod
    def _get_ocr_text(image_id: str) -> str:
        emb_path = settings.embeddings_path / f"{image_id}.json"
        if emb_path.exists():
            try:
                data = json.loads(emb_path.read_text(encoding="utf-8"))
                return data.get("full_text", "")
            except Exception:
                pass
        return ""

    def _generate_report(self, response: SearchResponse) -> None:
        report_dir = ensure_dir(settings._resolve("reports"))
        report = {
            "search_timestamp": datetime.now(timezone.utc).isoformat(),
            "query": response.query,
            "top_k": response.top_k,
            "retrieved_results": response.total_results,
            "search_latency_ms": response.timing.total_ms,
            "embedding_latency_ms": response.timing.query_embedding_ms,
            "vector_search_latency_ms": response.timing.vector_search_ms,
        }
        report_path = report_dir / "search_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Search report written to %s", report_path)
