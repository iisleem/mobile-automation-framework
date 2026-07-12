from __future__ import annotations


class ContextHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def contexts(self) -> list[str]:
        return list(self.driver.contexts)

    def current_context(self) -> str:
        return self.driver.current_context

    def switch_to_native(self) -> None:
        self.driver.switch_to.context("NATIVE_APP")

    def switch_to_webview(self, partial_name: str | None = None) -> str:
        for context in self.contexts():
            if "WEBVIEW" not in context and context.upper() != "CHROMIUM":
                continue
            if partial_name and partial_name not in context:
                continue
            self.driver.switch_to.context(context)
            return context
        raise AssertionError(f"No matching webview context found. Available: {self.contexts()}")
