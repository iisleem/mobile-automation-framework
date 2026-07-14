from __future__ import annotations

from typing import Callable, TypeVar

from automation_core.helpers import wait_until as core_wait_until


T = TypeVar("T")


def wait_until(
    condition: Callable[[], T | None | bool],
    timeout_seconds: float = 30,
    interval_seconds: float = 1,
    failure_message: str = "Condition was not met before timeout.",
) -> T:
    return core_wait_until(
        condition,
        timeout_seconds=timeout_seconds,
        interval_seconds=interval_seconds,
        failure_message=failure_message,
        ignore_exceptions=True,
    )
