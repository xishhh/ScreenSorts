from pathlib import Path
from typing import List


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_files(directory: Path, pattern: str = "*") -> List[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob(pattern))


def image_files(directory: Path) -> List[Path]:
    return find_files(directory, "*.[Pp][Nn][Gg]") + find_files(
        directory, "*.[Jj][Pp][Gg]"
    ) + find_files(directory, "*.[Jj][Pp][Ee][Gg]") + find_files(
        directory, "*.[Ww][Ee][Bb][Pp]"
    )


def zip_files(directory: Path) -> List[Path]:
    return find_files(directory, "*.[Zz][Ii][Pp]")
