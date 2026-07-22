import tarfile
import zipfile
from pathlib import Path
from typing import List, Tuple

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
ARCHIVE_EXTENSIONS = (".zip", ".tgz", ".tar.gz")


def discover_archives(datasets_dir: Path) -> List[Path]:
    if not datasets_dir.exists():
        return []
    archives: List[Path] = []
    for path in sorted(datasets_dir.iterdir()):
        if path.is_file() and _has_archive_ext(path):
            archives.append(path)
    return archives


def _has_archive_ext(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(ext) for ext in ARCHIVE_EXTENSIONS)


def dataset_name(path: Path) -> str:
    name = path.name
    for ext in (".tar.gz", ".tgz", ".zip"):
        if name.lower().endswith(ext):
            return name[: -len(ext)]
    return path.stem


def validate_archive(path: Path) -> bool:
    try:
        if path.name.lower().endswith(".zip"):
            with zipfile.ZipFile(path, "r") as zf:
                bad = zf.testzip()
                return bad is None
        else:
            with tarfile.open(path, "r:*") as tf:
                members = tf.getmembers()
                return len(members) > 0
    except Exception:
        return False


def list_images_in_archive(path: Path) -> List[str]:
    if path.name.lower().endswith(".zip"):
        return _list_images_in_zip(path)
    else:
        return _list_images_in_tar(path)


def _is_valid_image(name: str) -> bool:
    base = Path(name).name
    if base.startswith("._") or base.startswith("."):
        return False
    return name.lower().endswith(IMAGE_EXTENSIONS)


def _list_images_in_zip(path: Path) -> List[str]:
    with zipfile.ZipFile(path, "r") as zf:
        return [name for name in zf.namelist() if _is_valid_image(name)]


def _list_images_in_tar(path: Path) -> List[str]:
    with tarfile.open(path, "r:*") as tf:
        return [
            m.name
            for m in tf.getmembers()
            if m.isfile() and _is_valid_image(m.name)
        ]


def extract_image(archive_path: Path, image_path: str, output_dir: Path, dataset_prefix: str = "") -> Path:
    dest = _unique_path(output_dir, image_path, dataset_prefix)
    output_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.name.lower().endswith(".zip"):
        with zipfile.ZipFile(archive_path, "r") as zf:
            data = zf.read(image_path)
    else:
        with tarfile.open(archive_path, "r:*") as tf:
            member = tf.getmember(image_path)
            data = tf.extractfile(member)
            if data is None:
                raise OSError(f"Could not extract {image_path} from {archive_path.name}")
            data = data.read()
    dest.write_bytes(data)
    return dest


def extract_images_batch(archive_path: Path, image_paths: List[str], output_dir: Path, dataset_prefix: str = "") -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if archive_path.name.lower().endswith(".zip"):
        return [_extract_single_zip(archive_path, p, output_dir, dataset_prefix) for p in image_paths]
    else:
        return _extract_tar_batch(archive_path, image_paths, output_dir, dataset_prefix)


def _extract_single_zip(archive_path: Path, image_path: str, output_dir: Path, dataset_prefix: str) -> Path:
    dest = _unique_path(output_dir, image_path, dataset_prefix)
    with zipfile.ZipFile(archive_path, "r") as zf:
        dest.write_bytes(zf.read(image_path))
    return dest


def _extract_tar_batch(archive_path: Path, image_paths: List[str], output_dir: Path, dataset_prefix: str) -> List[Path]:
    wanted = set(image_paths)
    found: set = set()
    results: List[Path] = []
    with tarfile.open(archive_path, "r:*") as tf:
        for member in tf.getmembers():
            if member.name in wanted:
                data = tf.extractfile(member)
                if data is not None:
                    dest = _unique_path(output_dir, member.name, dataset_prefix)
                    dest.write_bytes(data.read())
                    results.append(dest)
                    found.add(member.name)
    missing = set(image_paths) - found
    if missing:
        raise OSError(f"Could not extract {len(missing)} image(s) from {archive_path.name}")
    return results


def _unique_path(output_dir: Path, original_path: str, dataset_prefix: str = "") -> Path:
    stem = Path(original_path).stem
    suffix = Path(original_path).suffix
    if dataset_prefix:
        stem = f"{dataset_prefix}_{stem}"
    dest = output_dir / f"{stem}{suffix}"
    counter = 1
    while dest.exists():
        dest = output_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    return dest
