from __future__ import annotations

import os
from pathlib import Path
import webbrowser


def open_report(path: Path, logger=None) -> bool:
    if _is_ci():
        if logger:
            logger.info("Skipping report auto-open in CI.")
        return False
    if not path.exists():
        return False
    return webbrowser.open(path.resolve().as_uri())


def _is_ci() -> bool:
    return os.getenv("CI", "").lower() in {"1", "true", "yes"}
