from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from screens.base_screen import BaseScreen


class LoginScreen(BaseScreen):
    @property
    def username(self):
        return self.locator_with_fallbacks(
            "Username field",
            (AppiumBy.ACCESSIBILITY_ID, "username"),
            (AppiumBy.ID, "com.example:id/username"),
        )

    @property
    def password(self):
        return self.locator_with_fallbacks(
            "Password field",
            (AppiumBy.ACCESSIBILITY_ID, "password"),
            (AppiumBy.ID, "com.example:id/password"),
        )

    @property
    def submit(self):
        return self.locator_with_fallbacks(
            "Login button",
            (AppiumBy.ACCESSIBILITY_ID, "login"),
            (AppiumBy.ID, "com.example:id/login"),
        )

    @property
    def success_message(self):
        return self.locator_with_fallbacks(
            "Success message",
            (AppiumBy.ACCESSIBILITY_ID, "login-success"),
            (AppiumBy.ID, "com.example:id/login_success"),
        )

    def login(self, username: str, password: str) -> None:
        self.type_text(self.username, username)
        self.type_text(self.password, password, sensitive=True)
        self.tap(self.submit, verify=self.success_message)
