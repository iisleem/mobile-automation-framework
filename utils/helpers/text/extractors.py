from __future__ import annotations

from automation_core.helpers import (
    extract_first_match as core_extract_first_match,
    extract_numbers as core_extract_numbers,
    extract_otp as core_extract_otp,
    normalize_text as core_normalize_text,
)


def extract_otp(text: str, regex: str = r"\b\d{4,8}\b") -> str | None:
    return core_extract_otp(text, regex)


def extract_first_match(text: str, regex: str) -> str | None:
    return core_extract_first_match(text, regex)


def extract_numbers(text: str) -> list[str]:
    return core_extract_numbers(text, allow_decimal=True)


def normalize_text(text: str) -> str:
    return core_normalize_text(text)
