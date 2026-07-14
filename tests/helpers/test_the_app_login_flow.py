from __future__ import annotations

import pytest

import flows.the_app.login_flows as login_flows
from flows.the_app import TheAppLoginFlow


pytestmark = pytest.mark.helpers


def test_login_flow_is_idempotent_when_rerun_starts_on_secret_screen(monkeypatch):
    events: list[str] = []

    class FakeHome:
        def __init__(self, driver) -> None:
            events.append("home-created")

    class FakeLogin:
        def __init__(self, driver=None) -> None:
            pass

        def is_loaded(self) -> bool:
            return False

        def assert_loaded(self) -> None:
            events.append("login-loaded")

        def login(self, username: str, password: str):
            events.append(f"login:{username}:{password}")
            return FakeLoggedInSecret()

    class FakeInitialSecret:
        def __init__(self, driver) -> None:
            pass

        def is_loaded(self) -> bool:
            return True

        def logout(self):
            events.append("logout")
            return FakeLogin()

    class FakeLoggedInSecret:
        def assert_logged_in_as(self, username: str) -> None:
            events.append(f"assert:{username}")

    monkeypatch.setattr(login_flows, "TheAppHomeScreen", FakeHome)
    monkeypatch.setattr(login_flows, "TheAppLoginScreen", FakeLogin)
    monkeypatch.setattr(login_flows, "TheAppSecretScreen", FakeInitialSecret)

    TheAppLoginFlow(driver=object()).login_successfully()

    assert events == ["logout", "login-loaded", "login:alice:mypassword", "assert:alice"]
