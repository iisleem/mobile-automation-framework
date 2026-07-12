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
    def __init__(self, contexts: list[str]) -> None:
        self.contexts = contexts
        self.current_context = contexts[0]
        self.switch_to = _SwitchTo()


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
