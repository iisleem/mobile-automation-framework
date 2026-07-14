from __future__ import annotations

import pytest

from utils.helpers.data import random_email, random_phone, random_username, timestamped_value, unique_id


pytestmark = pytest.mark.helpers


def test_data_generators_create_readable_unique_values():
    assert random_email().startswith("mobile.")
    assert random_email(domain="example.test").endswith("@example.test")
    assert random_username().startswith("mobile_")
    assert random_username(prefix="qa").startswith("qa_")
    assert random_phone(country_code="+962", digits=9).startswith("+962")
    assert len(random_phone(country_code="+962", digits=9)) == len("+962") + 9
    assert unique_id("run").startswith("run-")
    assert len(unique_id()) == len("id-") + 8
    assert timestamped_value("build").startswith("build-")
    assert "." not in timestamped_value("build")
