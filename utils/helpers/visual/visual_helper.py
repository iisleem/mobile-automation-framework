from __future__ import annotations

from pathlib import Path


def capture_screen_screenshot(driver, output_path: Path | str) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    driver.get_screenshot_as_file(str(path))
    return path


def assert_screenshot_matches_baseline(
    actual_path: Path | str,
    baseline_path: Path | str,
    update_baseline: bool = False,
) -> None:
    actual = Path(actual_path)
    baseline = Path(baseline_path)
    if update_baseline or not baseline.exists():
        baseline.parent.mkdir(parents=True, exist_ok=True)
        baseline.write_bytes(actual.read_bytes())
        return
    assert actual.read_bytes() == baseline.read_bytes(), f"Screenshot {actual} does not match baseline {baseline}"
