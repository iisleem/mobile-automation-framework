from __future__ import annotations

import time


class ContextHelper:
    def __init__(self, driver) -> None:
        self.driver = driver

    def contexts(self) -> list[object]:
        return list(self.driver.contexts)

    def detailed_contexts(self, wait_for_webview_ms: int = 0) -> list[object]:
        if not self._is_ios():
            return self.contexts()
        try:
            return list(self.driver.execute_script("mobile: getContexts", {"waitForWebviewMs": wait_for_webview_ms}))
        except Exception:
            return self.contexts()

    def current_context(self) -> str:
        return self.driver.current_context

    def switch_to_native(self) -> None:
        self.driver.switch_to.context("NATIVE_APP")

    def switch_to_webview(
        self,
        partial_name: str | None = None,
        title: str | None = None,
        url_contains: str | None = None,
        bundle_id: str | None = None,
        timeout_seconds: float = 15,
        poll_interval_seconds: float = 0.5,
    ) -> str:
        deadline = time.monotonic() + timeout_seconds
        last_contexts: list[object] = []
        while time.monotonic() <= deadline:
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            last_contexts = self.detailed_contexts(min(remaining_ms, int(poll_interval_seconds * 1000)))
            for context in last_contexts:
                context_name = self._context_id(context)
                if not self._is_webview_context(context):
                    continue
                if not self._matches(context, partial_name, title, url_contains, bundle_id):
                    continue
                self.driver.switch_to.context(context_name)
                return context_name
            time.sleep(poll_interval_seconds)
        raise AssertionError(
            "No matching webview context found. "
            f"Available: {last_contexts}. "
            "For iOS hybrid apps, verify WKWebView.isInspectable=true and add the app/process bundle id "
            "to appium:additionalWebviewBundleIds."
        )

    def _context_id(self, context) -> str:
        if isinstance(context, dict):
            return str(context.get("id") or context.get("name") or context.get("context") or "")
        return str(context)

    def _is_webview_context(self, context) -> bool:
        context_id = self._context_id(context)
        upper_context_id = context_id.upper()
        if "WEBVIEW" in upper_context_id or upper_context_id == "CHROMIUM":
            return True
        if not isinstance(context, dict) or upper_context_id == "NATIVE_APP":
            return False
        return bool(context.get("title") or context.get("url") or context.get("bundleId"))

    def _matches(
        self,
        context,
        partial_name: str | None,
        title: str | None,
        url_contains: str | None,
        bundle_id: str | None,
    ) -> bool:
        haystack = self._context_search_text(context).lower()
        checks = (partial_name, title, url_contains, bundle_id)
        return all(not value or value.lower() in haystack for value in checks)

    def _context_search_text(self, context) -> str:
        if isinstance(context, dict):
            return " ".join(str(value) for value in context.values() if value is not None)
        return str(context)

    def _is_ios(self) -> bool:
        capabilities = getattr(self.driver, "capabilities", {}) or {}
        return str(capabilities.get("platformName", "")).lower() == "ios"
