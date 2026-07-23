import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.schemas.demo import DemoComponentStatus, DemoStatusResponse
from app.services.vector_store_service import VectorStoreService
from app.utils.file_utils import ensure_dir, image_files


class DemoModeService:
    def __init__(self) -> None:
        self.demo_dir = settings.repo_demo_path
        self.metadata_dir = settings.repo_metadata_path
        self.ocr_dir = settings.ocr_results_path
        self.embeddings_dir = settings.embeddings_path
        self.vector_store = VectorStoreService()

    def check_readiness(self) -> DemoStatusResponse:
        corpus_status = self._check_corpus()
        ocr_status = self._check_ocr()
        emb_status = self._check_embeddings()
        index_status = self._check_index()

        screenshot_count = corpus_status.count
        datasets = []
        build_timestamp: Optional[str] = None
        if corpus_status.exists:
            datasets = self._get_datasets()
            build_timestamp = self._get_build_timestamp()

        all_ready = (
            corpus_status.exists
            and ocr_status.exists
            and emb_status.exists
            and index_status.exists
        )

        storage_bytes = self._total_storage_bytes()

        return DemoStatusResponse(
            ready=all_ready,
            screenshot_count=screenshot_count,
            dataset_count=len(datasets),
            datasets=datasets,
            total_storage_bytes=storage_bytes,
            build_timestamp=build_timestamp,
            corpus=corpus_status,
            ocr=ocr_status,
            embeddings=emb_status,
            index=index_status,
        )

    def _check_corpus(self) -> DemoComponentStatus:
        if not self.demo_dir.is_dir():
            return DemoComponentStatus(
                name="corpus", exists=False, details="Demo directory not found"
            )
        images = image_files(self.demo_dir)
        if not images:
            return DemoComponentStatus(
                name="corpus", exists=False, details="No demo images found"
            )
        manifest = self.demo_dir / "manifest.json"
        manifest_ok = manifest.exists()
        return DemoComponentStatus(
            name="corpus",
            exists=True,
            count=len(images),
            details=f"{len(images)} images" + (" (manifest present)" if manifest_ok else " (no manifest)"),
        )

    def _check_ocr(self) -> DemoComponentStatus:
        if not self.ocr_dir.is_dir():
            return DemoComponentStatus(
                name="ocr", exists=False, details="OCR results directory not found"
            )
        files = list(self.ocr_dir.glob("*.json"))
        return DemoComponentStatus(
            name="ocr",
            exists=len(files) > 0,
            count=len(files),
            details=f"{len(files)} OCR result(s)",
        )

    def _check_embeddings(self) -> DemoComponentStatus:
        if not self.embeddings_dir.is_dir():
            return DemoComponentStatus(
                name="embeddings", exists=False, details="Embeddings directory not found"
            )
        files = list(self.embeddings_dir.glob("*.json"))
        return DemoComponentStatus(
            name="embeddings",
            exists=len(files) > 0,
            count=len(files),
            details=f"{len(files)} embedding file(s)",
        )

    def _check_index(self) -> DemoComponentStatus:
        persist_dir = settings.chroma_persist_path
        if not persist_dir.is_dir():
            return DemoComponentStatus(
                name="index", exists=False, details="Vector store directory not found"
            )
        try:
            stats = self.vector_store.collection_stats()
            count = stats.get("document_count", 0)
            return DemoComponentStatus(
                name="index",
                exists=count > 0,
                count=count,
                details=f"{count} indexed document(s)",
            )
        except Exception as e:
            return DemoComponentStatus(
                name="index", exists=False, details=str(e)
            )

    def _get_datasets(self) -> list[str]:
        manifest_path = self.demo_dir / "manifest.json"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                return data.get("datasets", [])
            except Exception:
                pass
        datasets: set[str] = set()
        for meta_path in self.metadata_dir.glob("*.json"):
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                src = data.get("source_dataset", "")
                if src:
                    datasets.add(src)
            except Exception:
                pass
        return sorted(datasets)

    def _get_build_timestamp(self) -> Optional[str]:
        manifest_path = self.demo_dir / "manifest.json"
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                return data.get("build_timestamp")
            except Exception:
                pass
        return None

    def _total_storage_bytes(self) -> int:
        total = 0
        for path in [self.demo_dir, self.ocr_dir, self.embeddings_dir, settings.chroma_persist_path]:
            if path and path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        total += f.stat().st_size
        return total

    def generate_report(self) -> dict:
        status = self.check_readiness()
        report = {
            "report_timestamp": datetime.now(timezone.utc).isoformat(),
            "ready": status.ready,
            "screenshot_count": status.screenshot_count,
            "dataset_count": status.dataset_count,
            "datasets": status.datasets,
            "total_storage_bytes": status.total_storage_bytes,
            "build_timestamp": status.build_timestamp,
            "components": {
                "corpus": {
                    "exists": status.corpus.exists,
                    "count": status.corpus.count,
                    "details": status.corpus.details,
                },
                "ocr": {
                    "exists": status.ocr.exists,
                    "count": status.ocr.count,
                    "details": status.ocr.details,
                },
                "embeddings": {
                    "exists": status.embeddings.exists,
                    "count": status.embeddings.count,
                    "details": status.embeddings.details,
                },
                "index": {
                    "exists": status.index.exists,
                    "count": status.index.count,
                    "details": status.index.details,
                },
            },
            "overall_readiness": "ready" if status.ready else "incomplete",
        }
        report_dir = ensure_dir(settings._resolve("reports"))
        report_path = report_dir / "demo_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info("Demo report written to %s", report_path)
        return report
