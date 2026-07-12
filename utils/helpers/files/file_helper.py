from __future__ import annotations

from pathlib import Path
import shutil

from utils.helpers.wait import wait_until


def wait_for_file(directory: Path | str, pattern: str, timeout_seconds: float = 30) -> Path:
    root = Path(directory)
    return wait_until(
        lambda: next(root.glob(pattern), None),
        timeout_seconds=timeout_seconds,
        interval_seconds=0.5,
        failure_message=f"No file matching '{pattern}' appeared in {root}",
    )


def assert_file_exists(path: Path | str) -> Path:
    file_path = Path(path)
    assert file_path.exists() and file_path.is_file(), f"Expected file to exist: {file_path}"
    return file_path


def assert_file_extension(path: Path | str, extension: str) -> None:
    file_path = assert_file_exists(path)
    expected = extension if extension.startswith(".") else f".{extension}"
    assert file_path.suffix == expected, f"Expected {file_path} to end with {expected}"


def cleanup_directory(path: Path | str) -> Path:
    directory = Path(path)
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory
