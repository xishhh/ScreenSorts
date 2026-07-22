import argparse
import sys

from app.core.logging import logger
from app.services.demo_corpus_builder import DemoCorpusBuilder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the ScreenSorts demo corpus by sampling screenshots from local archives."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=None,
        help="Number of screenshots to sample per dataset (default: 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic sampling (default: 42)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover archives and show sample counts without extracting",
    )
    args = parser.parse_args()

    from app.core.config import settings

    if args.sample_size is not None:
        settings.demo_sample_size = args.sample_size
    if args.seed is not None:
        settings.demo_random_seed = args.seed

    if args.dry_run:
        _dry_run()
        return

    builder = DemoCorpusBuilder()
    builder.build()


def _dry_run() -> None:
    from app.core.config import settings
    from app.utils.archive_utils import discover_archives, dataset_name, list_images_in_archive, validate_archive

    archives = discover_archives(settings.repo_datasets_path)
    print(f"Datasets directory: {settings.repo_datasets_path}")
    print(f"Found {len(archives)} archive(s)\n")

    for archive in archives:
        name = dataset_name(archive)
        valid = validate_archive(archive)
        images = list_images_in_archive(archive) if valid else []
        sample = min(settings.demo_sample_size, len(images))
        status = "✓" if valid else "✗ CORRUPTED"
        print(f"  {status} {archive.name}")
        print(f"      Dataset:     {name}")
        print(f"      Size:        {archive.stat().st_size / (1024*1024):.1f} MB")
        print(f"      Images:      {len(images)}")
        print(f"      Sample:      {sample}")
        print()


if __name__ == "__main__":
    main()
