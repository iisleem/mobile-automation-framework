from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class SoftAssert:
    failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.failures.append(message)

    def equals(self, actual, expected, message: str | None = None) -> None:
        self.check(actual == expected, message or f"Expected {actual!r} to equal {expected!r}")

    def contains(self, container, item, message: str | None = None) -> None:
        self.check(item in container, message or f"Expected {container!r} to contain {item!r}")

    def assert_all(self) -> None:
        if self.failures:
            joined = "\n".join(f"{index}. {failure}" for index, failure in enumerate(self.failures, start=1))
            raise AssertionError(f"Soft assertion failures:\n{joined}")


@contextmanager
def soft_assert() -> Iterator[SoftAssert]:
    assertions = SoftAssert()
    yield assertions
    assertions.assert_all()
