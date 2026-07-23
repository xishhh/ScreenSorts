#!/usr/bin/env python3
"""CLI utility to validate Demo Mode readiness."""

import sys
from pathlib import Path

# Ensure backend root is on sys.path when run as a script
_backend_root = Path(__file__).resolve().parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from app.core.logging import logger  # noqa: E402
from app.services.demo_mode_service import DemoModeService  # noqa: E402


def main() -> None:
    service = DemoModeService()
    status = service.check_readiness()

    print()
    print("=" * 64)
    print("  ScreenSorts \u2014 Demo Mode Readiness Report")
    print("=" * 64)
    print()

    if status.ready:
        print("  Overall Status: READY")
    else:
        print("  Overall Status: NOT READY")
    print()

    print(f"  Screenshots:   {status.screenshot_count}")
    print(f"  Datasets:      {status.dataset_count}")
    if status.datasets:
        for ds in status.datasets:
            print(f"    - {ds}")
    print(f"  Storage:       {_format_bytes(status.total_storage_bytes)}")
    print(f"  Build:         {status.build_timestamp or 'N/A'}")
    print()

    print("  Components:")
    components = [status.corpus, status.ocr, status.embeddings, status.index]
    for comp in components:
        icon = "OK" if comp.exists else "XX"
        print(f"    {icon}  {comp.name:<12}  {comp.details}")
    print()

    if not status.ready:
        print("  Missing components:")
        for comp in components:
            if not comp.exists:
                print(f"    - {comp.name}: {comp.details}")
        print()
        print("  To rebuild the demo corpus, run:")
        print("    python -m app.scripts.build_demo_corpus")
        print()

    report = service.generate_report()
    print(f"  Report written to reports/demo_report.json")
    print()

    sys.exit(0 if status.ready else 1)


def _format_bytes(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} TB"


if __name__ == "__main__":
    main()
