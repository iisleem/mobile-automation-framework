from __future__ import annotations

from pathlib import Path

from automation_core.reporting import open_report as core_open_report


def open_report(path: Path, logger=None) -> bool:
    return core_open_report(path, logger)
