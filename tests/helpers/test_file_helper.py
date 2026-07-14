from __future__ import annotations

from pathlib import Path

import pytest

from utils.helpers.files import assert_file_extension, assert_file_exists, cleanup_directory, wait_for_file


pytestmark = pytest.mark.helpers


def test_file_helpers(tmp_path: Path):
    directory = cleanup_directory(tmp_path / "downloads")
    target = directory / "report.pdf"
    target.write_text("demo", encoding="utf-8")

    assert wait_for_file(directory, "*.pdf", timeout_seconds=1) == target
    assert assert_file_exists(target) == target
    assert_file_extension(target, ".pdf")
    assert cleanup_directory(directory) == directory
    assert directory.exists()
