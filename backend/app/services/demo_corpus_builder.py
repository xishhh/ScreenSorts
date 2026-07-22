import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.screenshot_metadata import ScreenshotMetadata
from app.repository.metadata_repository import MetadataRepository
from app.utils.archive_utils import (
    dataset_name,
    discover_archives,
    extract_images_batch,
    list_images_in_archive,
    validate_archive,
)
from app.utils.file_utils import ensure_dir


class DemoCorpusBuilder:
    def __init__(self) -> None:
        self.demo_dir = ensure_dir(settings.repo_demo_path)
        self.metadata_repo = MetadataRepository(settings.repo_metadata_path)
        self.sample_size = settings.demo_sample_size
        self.random_seed = settings.demo_random_seed
        self.archives: List[Path] = []
        self.stats: dict = {}

    def build(self) -> None:
        logger.info("Starting demo corpus build")
        logger.info(f"Sample size per dataset: {self.sample_size}")
        logger.info(f"Random seed: {self.random_seed}")

        self.archives = discover_archives(settings.repo_datasets_path)
        if not self.archives:
            logger.warning("No archives found in %s", settings.repo_datasets_path)
            return

        logger.info("Discovered %d archive(s)", len(self.archives))
        for archive in self.archives:
            logger.info("  %s (%s)", archive.name, dataset_name(archive))

        self._clear_demo_dir()

        total_extracted = 0
        per_dataset: dict = {}

        for archive in self.archives:
            name = dataset_name(archive)
            logger.info("Processing archive: %s", archive.name)

            if not validate_archive(archive):
                logger.error("Corrupted archive, skipping: %s", archive.name)
                per_dataset[name] = {"status": "failed", "reason": "corrupted archive"}
                continue

            image_paths = list_images_in_archive(archive)
            if not image_paths:
                logger.warning("No images found in %s", archive.name)
                per_dataset[name] = {"status": "skipped", "reason": "no images"}
                continue

            logger.info("Found %d images in %s", len(image_paths), archive.name)

            sample = self._sample(image_paths)
            logger.info(
                "Sampling %d images from %s", len(sample), archive.name
            )

            try:
                dests = extract_images_batch(archive, sample, self.demo_dir, dataset_prefix=name)
                for dest in dests:
                    self._init_metadata(dest, name)
                extracted = len(dests)
            except Exception:
                logger.exception("Failed to extract batch from %s", archive.name)
                extracted = 0

            per_dataset[name] = {"status": "success", "extracted": extracted}
            total_extracted += extracted
            logger.info(
                "Extracted %d images from %s", extracted, archive.name
            )

        self.stats = {
            "total_datasets": len(self.archives),
            "total_extracted": total_extracted,
            "per_dataset": per_dataset,
        }

        self._generate_manifest()

        logger.info("Demo corpus build complete")
        logger.info("Total screenshots extracted: %d", total_extracted)
        logger.info("Manifest written to: %s", self.demo_dir / "manifest.json")

    def _sample(self, items: List[str]) -> List[str]:
        rng = random.Random(self.random_seed)
        count = min(self.sample_size, len(items))
        return rng.sample(items, count)

    def _init_metadata(self, image_path: Path, source: str) -> None:
        metadata = ScreenshotMetadata(
            image_id=image_path.stem,
            image_path=str(image_path.relative_to(settings.repo_demo_path.parent)),
            source_dataset=source,
        )
        try:
            self.metadata_repo.create(metadata)
        except FileExistsError:
            pass

    def _generate_manifest(self) -> None:
        manifest = {
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
            "random_seed": self.random_seed,
            "sample_size": self.sample_size,
            "datasets": [dataset_name(a) for a in self.archives],
            "total_screenshots": self.stats.get("total_extracted", 0),
            "output_directory": str(self.demo_dir),
            "corpus_statistics": self.stats,
        }
        manifest_path = self.demo_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, default=str), encoding="utf-8"
        )

    def _clear_demo_dir(self) -> None:
        for child in self.demo_dir.iterdir():
            if child.name == ".gitkeep":
                continue
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                import shutil

                shutil.rmtree(child)
        for meta_path in settings.repo_metadata_path.glob("*.json"):
            meta_path.unlink()
