from __future__ import annotations

from screens.the_app import TheAppHomeScreen, TheAppLoginScreen, TheAppSecretScreen


class TheAppLoginFlow:
    def __init__(self, driver) -> None:
        self.driver = driver

    def login_successfully(self, username: str = "alice", password: str = "mypassword") -> None:
        login = self._ensure_login_screen()
        login.assert_loaded()
        secret = login.login(username, password)
        secret.assert_logged_in_as(username)

    def _ensure_login_screen(self) -> TheAppLoginScreen:
        secret = TheAppSecretScreen(self.driver)
        if secret.is_loaded():
            return secret.logout()

        login = TheAppLoginScreen(self.driver)
        if login.is_loaded():
            return login

        home = TheAppHomeScreen(self.driver)
        home.assert_loaded()
        return home.open_login()
