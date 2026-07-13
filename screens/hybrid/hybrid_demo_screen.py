from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from screens.base_screen import BaseScreen


class HybridNativeScreen(BaseScreen):
    @property
    def webview(self):
        return self.locator_with_fallbacks(
            "Hybrid demo webview",
            (AppiumBy.ACCESSIBILITY_ID, "Hybrid Demo WebView"),
            (AppiumBy.ACCESSIBILITY_ID, "hybridWebView"),
            (AppiumBy.CLASS_NAME, "android.webkit.WebView"),
            (AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeWebView"),
        )

    def expect_loaded(self) -> None:
        self.expect_visible(self.webview, "hybrid native webview")


class HybridWebScreen(BaseScreen):
    @property
    def name_input(self):
        return self.locator("css selector", "#name", "hybrid name input")

    @property
    def greet_button(self):
        return self.locator("css selector", "#greet", "hybrid greet button")

    @property
    def status(self):
        return self.locator("css selector", "#status", "hybrid status")

    def expect_page_loaded(self) -> None:
        assert "Hybrid Demo" in self.driver.title
        self.expect_visible(self.name_input, "hybrid web form")

    def submit_name(self, name: str) -> None:
        self.type_text(self.name_input, name)
        self.tap(self.greet_button, "Greet", verify=lambda: f"Hello, {name}" in self.text(self.status))

    def expect_greeting(self, name: str) -> None:
        self.expect_text_contains(self.status, f"Hello, {name}")
