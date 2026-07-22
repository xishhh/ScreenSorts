import json
import time
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.schemas.explain import (
    ExplainItem,
    ExplainRequest,
    ExplainResponse,
    ExplainTiming,
)
from app.schemas.search import SearchRequest, SearchResultItem
from app.services.explanation_cache import ExplanationCache
from app.services.groq_client import GroqClient, GroqClientError
from app.services.prompt_builder import PromptBuilder
from app.services.search_service import SearchService
from app.utils.file_utils import ensure_dir


class ExplanationService:
    def __init__(self) -> None:
        self.search_service = SearchService()
        self.prompt_builder = PromptBuilder()
        self.cache = ExplanationCache()
        self._groq_client: GroqClient | None = None

    def _get_groq_client(self) -> GroqClient:
        if self._groq_client is None:
            self._groq_client = GroqClient()
        return self._groq_client

    def explain(self, request: ExplainRequest) -> ExplainResponse:
        total_start = time.time()

        search_start = time.time()
        results = self._get_results(request)
        search_time = (time.time() - search_start) * 1000

        if not results:
            return ExplainResponse(
                query=request.query,
                top_k=request.top_k,
                threshold=request.threshold,
                total_explanations=0,
                explanations=[],
                timing=ExplainTiming(
                    search_ms=round(search_time, 2),
                    explain_ms=0,
                    total_ms=0,
                ),
            )

        explain_start = time.time()
        items = self._explain_batch(request.query, results)
        explain_time = (time.time() - explain_start) * 1000

        total_time = (time.time() - total_start) * 1000

        response = ExplainResponse(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
            total_explanations=len(items),
            explanations=items,
            timing=ExplainTiming(
                search_ms=round(search_time, 2),
                explain_ms=round(explain_time, 2),
                total_ms=round(total_time, 2),
            ),
        )

        self._generate_report(request, response)
        return response

    def _get_results(self, request: ExplainRequest) -> list[dict[str, Any]]:
        if request.image_ids:
            return self._get_results_by_ids(request.image_ids)
        return self._get_results_by_search(request)

    def _get_results_by_search(
        self, request: ExplainRequest
    ) -> list[dict[str, Any]]:
        search_req = SearchRequest(
            query=request.query,
            top_k=request.top_k,
            threshold=request.threshold,
        )
        search_resp = self.search_service.search(search_req)
        return [
            {
                "image_id": r.image_id,
                "image_path": r.image_path,
                "text": r.text,
                "score": r.score,
                "source_dataset": r.source_dataset,
            }
            for r in search_resp.results
        ]

    def _get_results_by_ids(
        self, image_ids: list[str]
    ) -> list[dict[str, Any]]:
        import json as _json

        results: list[dict[str, Any]] = []
        for image_id in image_ids:
            emb_path = settings.embeddings_path / f"{image_id}.json"
            if not emb_path.exists():
                continue
            try:
                data = _json.loads(emb_path.read_text(encoding="utf-8"))
                results.append(
                    {
                        "image_id": image_id,
                        "image_path": data.get("image_path", str(image_id)),
                        "text": data.get("full_text", ""),
                        "score": 0.0,
                        "source_dataset": data.get("source_dataset", ""),
                    }
                )
            except Exception:
                logger.warning("Failed to load embedding data for %s", image_id)
        return results

    def _explain_batch(
        self, query: str, results: list[dict[str, Any]]
    ) -> list[ExplainItem]:
        items: list[ExplainItem] = []
        for result in results:
            item = self._explain_single(query, result)
            items.append(item)
        return items

    def _explain_single(
        self, query: str, result: dict[str, Any]
    ) -> ExplainItem:
        image_id = result.get("image_id", "")
        text = result.get("text", "")
        score = result.get("score", 0.0)

        cached = self.cache.get(query, image_id, self._get_groq_client().model)
        if cached is not None:
            return ExplainItem(
                image_id=image_id,
                image_path=result.get("image_path", ""),
                text=text,
                score=score,
                source_dataset=result.get("source_dataset", ""),
                explanation=cached,
                model=self._get_groq_client().model,
                cache_hit=True,
                latency_ms=0,
            )

        explain_start = time.time()
        explanation, usage_info = self._call_groq(query, result)
        latency = (time.time() - explain_start) * 1000

        self.cache.set(query, image_id, self._get_groq_client().model, explanation)

        return ExplainItem(
            image_id=image_id,
            image_path=result.get("image_path", ""),
            text=text,
            score=score,
            source_dataset=result.get("source_dataset", ""),
            explanation=explanation,
            model=usage_info.get("model", self._get_groq_client().model),
            cache_hit=False,
            latency_ms=round(latency, 2),
        )

    def _call_groq(
        self, query: str, result: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        text = result.get("text", "")
        score = result.get("score", 0.0)
        image_id = result.get("image_id", "")
        image_path = result.get("image_path", "")
        source_dataset = result.get("source_dataset", "")

        metadata_str = self.prompt_builder.build_metadata_str(
            image_id, image_path, source_dataset
        )
        messages = self.prompt_builder.build_explain_messages(
            query, text, metadata_str, score
        )

        client = self._get_groq_client()
        explanation, usage_info = client.complete(messages)
        return explanation, usage_info

    def summarize(
        self, query: str, items: list[ExplainItem]
    ) -> str:
        explanations_text = "\n".join(
            f"- {item.image_id} (score {item.score:.4f}): {item.explanation}"
            for item in items
            if item.explanation
        )
        if not explanations_text:
            return "No explanations available to summarize."

        messages = self.prompt_builder.build_summarize_messages(
            query, explanations_text
        )
        try:
            client = self._get_groq_client()
            summary, _ = client.complete(messages)
            return summary
        except GroqClientError as e:
            logger.error("Summarization failed: %s", e)
            return ""

    def _generate_report(
        self, request: ExplainRequest, response: ExplainResponse
    ) -> None:
        report_dir = ensure_dir(settings._resolve("reports"))
        report = {
            "explain_timestamp": datetime.now(timezone.utc).isoformat(),
            "query": request.query,
            "top_k": request.top_k,
            "threshold": request.threshold,
            "specific_image_ids": request.image_ids,
            "total_explanations": response.total_explanations,
            "search_latency_ms": response.timing.search_ms,
            "explain_latency_ms": response.timing.explain_ms,
            "total_latency_ms": response.timing.total_ms,
            "cache_hits": sum(1 for e in response.explanations if e.cache_hit),
            "cache_misses": sum(1 for e in response.explanations if not e.cache_hit),
            "model": self._get_groq_client().model,
        }
        report_path = report_dir / "explanation_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Explanation report written to %s", report_path)
