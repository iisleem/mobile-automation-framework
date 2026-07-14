from __future__ import annotations

from automation_core.helpers import (
    random_email as core_random_email,
    random_phone as core_random_phone,
    random_username as core_random_username,
    timestamped_value as core_timestamped_value,
    unique_id as core_unique_id,
)


def unique_id(prefix: str = "id", length: int = 8) -> str:
    return core_unique_id(prefix=prefix, length=length)


def timestamped_value(prefix: str = "value") -> str:
    return core_timestamped_value(prefix=prefix, timestamp_format="%Y%m%d%H%M%S", include_microseconds=False)


def random_email(domain: str = "example.test", prefix: str = "mobile") -> str:
    return core_random_email(domain=domain, prefix=prefix)


def random_username(prefix: str = "mobile") -> str:
    return core_random_username(prefix=prefix, length=8)


def random_phone(country_code: str = "+962", digits: int = 9) -> str:
    return core_random_phone(country_code=country_code, digits=digits)
