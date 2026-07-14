from __future__ import annotations

import logging
import sys

from automation_core.logger import get_logger as core_get_logger


def get_logger(name: str) -> logging.Logger:
    return core_get_logger(name, stream=sys.stdout)
