from __future__ import annotations

import pytest

from utils.helpers.contexts import ContextHelper


pytestmark = pytest.mark.helpers


class _SwitchTo:
    def __init__(self) -> None:
        self.selected = None

    def context(self, value: str) -> None:
        self.selected = value


class _Driver:
    def __init__(self, contexts: list[object], capabilities: dict | None = None) -> None:
        self.contexts = contexts
        self.current_context = contexts[0]
        self.capabilities = capabilities or {}
        self.switch_to = _SwitchTo()

    def execute_script(self, script: str, args: dict | None = None):
        raise NotImplementedError(script)


class _DelayedContextDriver:
    def __init__(self) -> None:
        self.calls = 0
        self.current_context = "NATIVE_APP"
        self.capabilities = {}
        self.switch_to = _SwitchTo()

    @property
    def contexts(self) -> list[str]:
        self.calls += 1
        if self.calls == 1:
            return ["NATIVE_APP"]
        return ["NATIVE_APP", "WEBVIEW_delayed"]


def test_context_helper_switches_to_native():
    driver = _Driver(["WEBVIEW_com.example", "NATIVE_APP"])

    ContextHelper(driver).switch_to_native()

    assert driver.switch_to.selected == "NATIVE_APP"


def test_context_helper_switches_to_matching_webview():
    driver = _Driver(["NATIVE_APP", "WEBVIEW_com.example"])

    context = ContextHelper(driver).switch_to_webview("example")

    assert context == "WEBVIEW_com.example"
    assert driver.switch_to.selected == "WEBVIEW_com.example"


def test_context_helper_supports_android_chromium_context():
    driver = _Driver(["NATIVE_APP", "CHROMIUM"])

    context = ContextHelper(driver).switch_to_webview()

    assert context == "CHROMIUM"


def test_context_helper_waits_for_delayed_webview_context():
    driver = _DelayedContextDriver()

    context = ContextHelper(driver).switch_to_webview(timeout_seconds=1, poll_interval_seconds=0)

    assert context == "WEBVIEW_delayed"
    assert driver.switch_to.selected == "WEBVIEW_delayed"


def test_context_helper_supports_full_context_list_dictionaries():
    driver = _Driver([{"id": "NATIVE_APP"}, {"id": "WEBVIEW_dev.mobileframework.hybriddemo"}])

    context = ContextHelper(driver).switch_to_webview("hybriddemo")

    assert context == "WEBVIEW_dev.mobileframework.hybriddemo"
    assert driver.switch_to.selected == "WEBVIEW_dev.mobileframework.hybriddemo"


def test_context_helper_uses_ios_mobile_get_contexts_metadata():
    class IosDriver(_Driver):
        def __init__(self) -> None:
            super().__init__(["NATIVE_APP"], capabilities={"platformName": "iOS"})

        def execute_script(self, script: str, args: dict | None = None):
            assert script == "mobile: getContexts"
            assert args == {"waitForWebviewMs": 0}
            return [
                {"id": "NATIVE_APP"},
                {
                    "id": "WEBVIEW_17506.1",
                    "title": "Hybrid Demo",
                    "url": "https://hybrid.demo.local/",
                    "bundleId": "process-HybridDemo",
                },
            ]

    driver = IosDriver()

    context = ContextHelper(driver).switch_to_webview(
        title="Hybrid Demo",
        url_contains="hybrid.demo.local",
        bundle_id="process-HybridDemo",
        timeout_seconds=1,
        poll_interval_seconds=0,
    )

    assert context == "WEBVIEW_17506.1"
    assert driver.switch_to.selected == "WEBVIEW_17506.1"
