from __future__ import annotations

import time
from typing import Callable, TypeVar


T = TypeVar("T")


def wait_until(
    condition: Callable[[], T | None | bool],
    timeout_seconds: float = 30,
    interval_seconds: float = 1,
    failure_message: str = "Condition was not met before timeout.",
) -> T:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() <= deadline:
        try:
            result = condition()
            if result:
                return result  # type: ignore[return-value]
        except Exception as error:
            last_error = error
        time.sleep(interval_seconds)

    if last_error:
        raise TimeoutError(f"{failure_message} Last error: {last_error}") from last_error
    raise TimeoutError(failure_message)
