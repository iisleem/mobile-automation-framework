from __future__ import annotations

import re


def extract_otp(text: str, regex: str = r"\b\d{4,8}\b") -> str | None:
    return extract_first_match(text, regex)


def extract_first_match(text: str, regex: str) -> str | None:
    match = re.search(regex, text)
    if not match:
        return None
    if match.groups():
        return match.group(1)
    return match.group(0)


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?", text)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
