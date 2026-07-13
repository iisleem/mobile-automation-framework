from __future__ import annotations

from screens.login_screen import LoginScreen


class LoginFlow:
    def __init__(self, driver) -> None:
        self.driver = driver

    def login_successfully(self) -> None:
        LoginScreen(self.driver).login("demo@example.test", "password")
