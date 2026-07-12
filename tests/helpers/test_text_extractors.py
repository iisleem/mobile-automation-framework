from __future__ import annotations

import pytest

from utils.helpers.text import extract_first_match, extract_numbers, extract_otp, normalize_text


pytestmark = pytest.mark.helpers


def test_extract_otp_uses_default_pattern():
    assert extract_otp("Your code is 482913") == "482913"


def test_extract_first_match_returns_capture_group():
    assert extract_first_match("Order ID: ORD-123", r"Order ID: ([A-Z]+-\d+)") == "ORD-123"


def test_extract_numbers_and_normalize_text():
    assert extract_numbers("Total 42, tax 3.5") == ["42", "3.5"]
    assert normalize_text("Hello   mobile\nteam") == "Hello mobile team"
