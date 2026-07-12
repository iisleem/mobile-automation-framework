from __future__ import annotations

from screens.the_app import TheAppHomeScreen


class TheAppLoginFlow:
    def __init__(self, driver) -> None:
        self.driver = driver

    def login_successfully(self, username: str = "alice", password: str = "mypassword") -> None:
        home = TheAppHomeScreen(self.driver)
        home.assert_loaded()
        login = home.open_login()
        login.assert_loaded()
        secret = login.login(username, password)
        secret.assert_logged_in_as(username)
