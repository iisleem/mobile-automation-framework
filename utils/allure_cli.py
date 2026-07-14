from __future__ import annotations

from pathlib import Path
import shutil


def get_allure_cli(project_root: Path, logger=None) -> str | None:
    executable = shutil.which("allure")
    if executable:
        return executable
    if logger:
        logger.warning("Allure CLI was not found. Core product reports remain available; official Allure is optional.")
    return None
