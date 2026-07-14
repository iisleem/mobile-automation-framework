from __future__ import annotations

from pathlib import Path

from automation_core.reporting import get_or_install_allure_cli


def get_allure_cli(project_root: Path, logger=None) -> str | None:
    return get_or_install_allure_cli(project_root, logger, install_if_missing=False)
