from __future__ import annotations

import pytest

from utils.helpers.soft_assertions import SoftAssert, soft_assert


pytestmark = pytest.mark.helpers


def test_soft_assert_collects_failures():
    assertions = SoftAssert()
    assertions.equals("android", "ios")
    assertions.contains(["native"], "hybrid")
    with pytest.raises(AssertionError) as error:
        assertions.assert_all()
    assert "Soft assertion failures" in str(error.value)


def test_soft_assert_context_passes_when_clean():
    with soft_assert() as assertions:
        assertions.equals("mobile", "mobile")
