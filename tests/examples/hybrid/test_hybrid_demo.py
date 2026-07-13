from __future__ import annotations

import pytest

from screens.hybrid import HybridNativeScreen, HybridWebScreen
from utils.helpers.contexts import ContextHelper


pytestmark = [pytest.mark.hybrid, pytest.mark.smoke]


def test_hybrid_demo_switches_context_and_submits_form(mobile_driver):
    native = HybridNativeScreen(mobile_driver)
    native.expect_loaded()

    contexts = ContextHelper(mobile_driver)
    try:
        webview_context = contexts.switch_to_webview()
    except AssertionError as error:
        if str(mobile_driver.capabilities.get("platformName", "")).lower() == "ios":
            pytest.skip(f"iOS WKWebView loaded, but Appium did not expose a WEBVIEW context here: {error}")
        raise
    assert "WEBVIEW" in webview_context.upper() or webview_context.upper() == "CHROMIUM"

    web = HybridWebScreen(mobile_driver)
    web.expect_page_loaded()
    web.submit_name("Hybrid QA")
    web.expect_greeting("Hybrid QA")

    contexts.switch_to_native()
    native.expect_loaded()
