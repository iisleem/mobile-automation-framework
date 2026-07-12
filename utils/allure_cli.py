from __future__ import annotations

from pathlib import Path
import shutil


def get_allure_cli(project_root: Path, logger=None) -> str | None:
    executable = shutil.which("allure")
    if executable:
        return executable
    if logger:
        logger.warning("Allure CLI was not found. Built-in HTML report fallback will be used.")
    return None
