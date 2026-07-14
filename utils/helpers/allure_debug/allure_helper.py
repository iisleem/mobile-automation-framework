from __future__ import annotations

from automation_core.reporting import attach_json as core_attach_json
from automation_core.reporting import attach_text as core_attach_text
from automation_core.reporting import step

__all__ = ["attach_json", "attach_text", "step"]


def attach_text(name: str, value: str) -> None:
    core_attach_text(value, name=name)


def attach_json(name: str, value) -> None:
    core_attach_json(value, name=name)
