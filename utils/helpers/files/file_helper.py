from __future__ import annotations

from pathlib import Path

from automation_core.helpers import (
    assert_file_exists as core_assert_file_exists,
    assert_file_extension as core_assert_file_extension,
    cleanup_directory as core_cleanup_directory,
    wait_for_file as core_wait_for_file,
)


def wait_for_file(directory: Path | str, pattern: str, timeout_seconds: float = 30) -> Path:
    return core_wait_for_file(directory, pattern, timeout_seconds=timeout_seconds, interval_seconds=0.5)


def assert_file_exists(path: Path | str) -> Path:
    return core_assert_file_exists(path)


def assert_file_extension(path: Path | str, extension: str) -> None:
    core_assert_file_extension(path, extension)


def cleanup_directory(path: Path | str) -> Path:
    return core_cleanup_directory(path, recreate=True)
