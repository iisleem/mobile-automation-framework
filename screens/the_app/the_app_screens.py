from __future__ import annotations

from appium.webdriver.common.appiumby import AppiumBy

from screens.base_screen import BaseScreen


class TheAppHomeScreen(BaseScreen):
    @property
    def login_screen_item(self):
        return self.locator_with_fallbacks(
            "Login Screen menu item",
            (AppiumBy.ACCESSIBILITY_ID, "Login Screen"),
            (AppiumBy.XPATH, "//*[@text='Login Screen' or @name='Login Screen']"),
        )

    def assert_loaded(self) -> None:
        self.expect_visible(self.login_screen_item, "TheApp home")

    def open_login(self) -> "TheAppLoginScreen":
        login_screen = TheAppLoginScreen(self.driver, self.settings)
        self.tap(self.login_screen_item, "Login Screen", verify=login_screen.username_field)
        return login_screen


class TheAppLoginScreen(BaseScreen):
    @property
    def username_field(self):
        return self.locator_with_fallbacks(
            "Username field",
            (AppiumBy.IOS_PREDICATE, 'type == "XCUIElementTypeTextField" AND (name == "username" OR label == "username")'),
            (AppiumBy.ACCESSIBILITY_ID, "username"),
            (AppiumBy.XPATH, "//*[@name='username' or @resource-id='username']"),
        )

    @property
    def password_field(self):
        return self.locator_with_fallbacks(
            "Password field",
            (
                AppiumBy.IOS_PREDICATE,
                'type == "XCUIElementTypeSecureTextField" AND (name == "password" OR label == "password")',
            ),
            (AppiumBy.ACCESSIBILITY_ID, "password"),
            (AppiumBy.XPATH, "//*[@name='password' or @resource-id='password']"),
        )

    @property
    def login_button(self):
        return self.locator_with_fallbacks(
            "Login button",
            (AppiumBy.ACCESSIBILITY_ID, "loginBtn"),
            (AppiumBy.XPATH, "//*[@name='loginBtn' or @resource-id='loginBtn']"),
        )

    def assert_loaded(self) -> None:
        self.expect_visible(self.username_field, "Login screen")

    def login(self, username: str, password: str) -> "TheAppSecretScreen":
        self.type_text(self.username_field, username, description="Username")
        if str(self.driver.capabilities.get("platformName", "")).lower() == "ios":
            self.type_text_with_keyboard(
                self.password_field,
                password,
                clear_first=False,
                description="Password",
                sensitive=True,
            )
        else:
            self.type_text(self.password_field, password, description="Password", sensitive=True)
        self.hide_keyboard()
        secret_screen = TheAppSecretScreen(self.driver, self.settings)
        self.tap(self.login_button, "Login", verify=secret_screen.logged_in_message)
        return secret_screen


class TheAppSecretScreen(BaseScreen):
    @property
    def logged_in_message(self):
        return self.locator_with_fallbacks(
            "Logged-in message",
            (AppiumBy.XPATH, '//*[contains(@text, "You are logged in as") or contains(@name, "You are logged in as")]'),
            (AppiumBy.XPATH, '//*[contains(@content-desc, "Logged in as") or contains(@label, "Logged in as")]'),
        )

    @property
    def logout_button(self):
        return self.locator_with_fallbacks(
            "Logout button",
            (AppiumBy.ACCESSIBILITY_ID, "Logout"),
            (AppiumBy.XPATH, "//*[@text='Logout' or @name='Logout']"),
        )

    def assert_logged_in_as(self, username: str) -> None:
        self.expect_visible(self.logged_in_message, "Logged-in message")
        self.assert_source_contains(username)

    def logout(self) -> TheAppLoginScreen:
        self.tap(self.logout_button, "Logout")
        return TheAppLoginScreen(self.driver, self.settings)
