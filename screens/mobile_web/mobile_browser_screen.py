from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from screens.base_screen import BaseScreen


class MobileBrowserScreen(BaseScreen):
    name_input = (By.CSS_SELECTOR, "#name")
    greet_button = (By.CSS_SELECTOR, "#greet")
    status_message = (By.CSS_SELECTOR, "#status")

    def open_url(self, url: str) -> None:
        self.driver.get(url)

    def enter_name(self, name: str) -> None:
        self.type_text(self.locator(*self.name_input, "name input"), name)

    def submit_greeting(self) -> None:
        self.tap(self.locator(*self.greet_button, "greet button"))

    def assert_status_contains(self, expected_text: str) -> None:
        self.expect_text_contains(self.locator(*self.status_message, "status message"), expected_text)

    def assert_title_contains(self, expected_text: str) -> None:
        wait = WebDriverWait(self.driver, self._default_timeout_ms() / 1000)
        wait.until(lambda driver: expected_text in driver.title)

    def assert_url_contains(self, expected_text: str) -> None:
        actual = self.driver.current_url
        assert expected_text in actual, f"Expected mobile browser URL {actual!r} to contain {expected_text!r}"
