from __future__ import annotations

import pytest

from utils.helpers.wait import wait_until


pytestmark = pytest.mark.helpers


def test_wait_until_returns_truthy_value():
    attempts = {"count": 0}

    def condition():
        attempts["count"] += 1
        return "ready" if attempts["count"] == 2 else None

    assert wait_until(condition, timeout_seconds=1, interval_seconds=0.01) == "ready"


def test_wait_until_raises_timeout():
    with pytest.raises(TimeoutError):
        wait_until(lambda: None, timeout_seconds=0.02, interval_seconds=0.01)
