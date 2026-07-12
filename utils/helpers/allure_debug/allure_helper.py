from __future__ import annotations

from contextlib import contextmanager
import json
from typing import Iterator


@contextmanager
def step(title: str) -> Iterator[None]:
    try:
        import allure
    except Exception:
        yield
        return

    with allure.step(title):
        yield


def attach_text(name: str, value: str) -> None:
    try:
        import allure

        allure.attach(value, name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:
        return


def attach_json(name: str, value) -> None:
    try:
        import allure

        allure.attach(
            json.dumps(value, indent=2, sort_keys=True),
            name=name,
            attachment_type=allure.attachment_type.JSON,
        )
    except Exception:
        return
