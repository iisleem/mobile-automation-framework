from __future__ import annotations

import time


class ContextHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def contexts(self) -> list[object]:
        return list(self.driver.contexts)

    def current_context(self) -> str:
        return self.driver.current_context

    def switch_to_native(self) -> None:
        self.driver.switch_to.context("NATIVE_APP")

    def switch_to_webview(
        self,
        partial_name: str | None = None,
        timeout_seconds: float = 15,
        poll_interval_seconds: float = 0.5,
    ) -> str:
        deadline = time.monotonic() + timeout_seconds
        last_contexts: list[object] = []
        while time.monotonic() <= deadline:
            last_contexts = self.contexts()
            for context in last_contexts:
                context_name = self._context_name(context)
                if "WEBVIEW" not in context_name and context_name.upper() != "CHROMIUM":
                    continue
                if partial_name and partial_name not in context_name:
                    continue
                self.driver.switch_to.context(context_name)
                return context_name
            time.sleep(poll_interval_seconds)
        raise AssertionError(f"No matching webview context found. Available: {last_contexts}")

    def _context_name(self, context) -> str:
        if isinstance(context, dict):
            return str(context.get("id") or context.get("name") or context.get("context") or "")
        return str(context)
