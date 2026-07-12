from __future__ import annotations

from datetime import datetime, timezone
import random
import string
import uuid


def unique_id(prefix: str = "id", length: int = 8) -> str:
    suffix = uuid.uuid4().hex[:length]
    return f"{prefix}-{suffix}" if prefix else suffix


def timestamped_value(prefix: str = "value") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{stamp}"


def random_email(domain: str = "example.test", prefix: str = "mobile") -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@{domain}"


def random_username(prefix: str = "mobile") -> str:
    token = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}_{token}"


def random_phone(country_code: str = "+962", digits: int = 9) -> str:
    number = "".join(random.choices(string.digits, k=digits))
    return f"{country_code}{number}"
