from __future__ import annotations

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, WebDriverException

import screens.base_screen as base_screen
from screens.base_screen import BaseScreen


pytestmark = pytest.mark.helpers


class _Driver:
    def __init__(self, platform_name: str) -> None:
        self.capabilities = {"platformName": platform_name}


class _KeyboardDriver(_Driver):
    def __init__(self, element: "_Element") -> None:
        super().__init__("iOS")
        self.element = element
        self.scripts: list[tuple[str, object]] = []

    def execute_script(self, script: str, args=None):
        self.scripts.append((script, args))
        if script == "mobile: keys":
            keys = args.get("keys", []) if isinstance(args, dict) else []
            self.element.value = "•" * len(keys)
            return None
        if script == "return arguments[0].value":
            return self.element.value
        return None


class _Element:
    def __init__(self, value: str = "", package_name: str = "") -> None:
        self.value = value
        self.package_name = package_name
        self.property_value = ""
        self.click_calls = 0
        self.clear_calls = 0
        self.send_keys_calls = 0
        self.failed_send_attempts = 0
        self.failed_click_attempts = 0

    def click(self) -> None:
        self.click_calls += 1
        if self.failed_click_attempts:
            self.failed_click_attempts -= 1
            raise WebDriverException("tap did not land")

    def clear(self) -> None:
        self.clear_calls += 1
        self.value = ""

    def send_keys(self, value: str) -> None:
        self.send_keys_calls += 1
        if self.failed_send_attempts:
            self.failed_send_attempts -= 1
            return
        self.value = value

    def get_attribute(self, name: str) -> str:
        if name == "package":
            return self.package_name
        if name == "value":
            return self.value
        return ""

    def get_property(self, name: str) -> str:
        if name == "value":
            return self.property_value
        return ""

    @property
    def text(self) -> str:
        return self.value


class _DialogDriver(_Driver):
    def __init__(self, button: "_Element", button_text: str = "Wait") -> None:
        super().__init__("Android")
        self.button = button
        self.button_text = button_text
        self.find_elements_calls = 0

    def find_elements(self, by: str, value: str):
        self.find_elements_calls += 1
        if self.button_text in value and self.button.click_calls == 0:
            return [self.button]
        return []


def test_base_screen_skips_ios_only_locators_on_android():
    screen = BaseScreen(_Driver("Android"), settings={})
    locators = (
        screen.locator(AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeTextField'", "iOS field"),
        screen.locator(AppiumBy.ACCESSIBILITY_ID, "username", "Username"),
        screen.locator(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Username")', "Android field"),
    )

    supported = screen._supported_locators(locators)

    assert [locator.by for locator in supported] == [AppiumBy.ACCESSIBILITY_ID, AppiumBy.ANDROID_UIAUTOMATOR]


def test_base_screen_skips_android_only_locators_on_ios():
    screen = BaseScreen(_Driver("iOS"), settings={})
    locators = (
        screen.locator(AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeTextField'", "iOS field"),
        screen.locator(AppiumBy.ACCESSIBILITY_ID, "username", "Username"),
        screen.locator(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("Username")', "Android field"),
    )

    supported = screen._supported_locators(locators)

    assert [locator.by for locator in supported] == [AppiumBy.IOS_PREDICATE, AppiumBy.ACCESSIBILITY_ID]


def test_type_text_retries_when_send_keys_does_not_change_value():
    element = _Element()
    element.failed_send_attempts = 1
    screen = BaseScreen(
        _Driver("Android"),
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.type_text(screen.accessibility_id("username", "Username"), "alice")

    assert element.send_keys_calls == 2
    assert element.value == "alice"


def test_type_text_fails_on_the_action_when_value_never_changes():
    element = _Element()
    element.failed_send_attempts = 3
    screen = BaseScreen(
        _Driver("Android"),
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    with pytest.raises(AssertionError, match="Type into Username failed after 3 attempts"):
        screen.type_text(screen.accessibility_id("username", "Username"), "alice")

    assert element.send_keys_calls == 3


def test_tap_retries_command_failures():
    element = _Element()
    element.failed_click_attempts = 2
    screen = BaseScreen(
        _Driver("Android"),
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.tap(screen.accessibility_id("loginBtn", "Login"))

    assert element.click_calls == 3


def test_tap_dismisses_android_system_dialogs():
    element = _Element()
    dialog_button = _Element(package_name="android")
    driver = _DialogDriver(dialog_button)
    screen = BaseScreen(
        driver,
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.tap(screen.accessibility_id("loginBtn", "Login"))

    assert dialog_button.click_calls == 1
    assert element.click_calls == 1


def test_android_system_dialogs_do_not_click_close_app():
    element = _Element()
    dialog_button = _Element()
    driver = _DialogDriver(dialog_button, button_text="Close app")
    screen = BaseScreen(
        driver,
        settings={"retries": {"action_default": 1, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.tap(screen.accessibility_id("loginBtn", "Login"))

    assert dialog_button.click_calls == 0
    assert element.click_calls == 1


def test_android_system_dialogs_skip_app_owned_buttons():
    element = _Element()
    dialog_button = _Element(package_name="com.example.app")
    driver = _DialogDriver(dialog_button, button_text="OK")
    screen = BaseScreen(
        driver,
        settings={"retries": {"action_default": 1, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.tap(screen.accessibility_id("loginBtn", "Login"))

    assert dialog_button.click_calls == 0
    assert element.click_calls == 1


def test_tap_retries_when_post_action_verification_fails_then_passes():
    element = _Element()
    verify_calls = 0
    screen = BaseScreen(
        _Driver("Android"),
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    def verify_loaded() -> bool:
        nonlocal verify_calls
        verify_calls += 1
        return verify_calls > 1

    screen.tap(screen.accessibility_id("loginBtn", "Login"), verify=verify_loaded)

    assert element.click_calls == 2
    assert verify_calls == 2


def test_type_text_with_keyboard_uses_ios_mobile_keys_and_verifies_masked_value():
    element = _Element()
    driver = _KeyboardDriver(element)
    screen = BaseScreen(
        driver,
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen.type_text_with_keyboard(
        screen.accessibility_id("password", "Password"),
        "secret",
        sensitive=True,
    )

    script_names = [script for script, _args in driver.scripts]
    assert "mobile: configureLocalization" in script_names
    assert ("mobile: keys", {"keys": list("secret")}) in driver.scripts
    assert element.value == "••••••"


def test_self_healing_uses_fallback_locator_when_primary_times_out(monkeypatch):
    element = _Element()
    warnings: list[tuple[object, ...]] = []
    screen = BaseScreen(
        _Driver("Android"),
        settings={
            "timeouts": {"default_timeout_ms": 1000},
            "self_healing": {"enabled": True, "timeout_ms": 100},
        },
    )
    primary = screen.accessibility_id("oldLogin", "Login button old id")
    fallback = screen.accessibility_id("loginBtn", "Login button fallback id")
    locator = screen.locator_with_fallbacks("Login button", primary, fallback)

    def wait_for(candidate, timeout_ms):
        if candidate.value == "oldLogin":
            raise TimeoutException("primary locator missing")
        return element

    monkeypatch.setattr(screen, "_wait_for", wait_for)
    monkeypatch.setattr(base_screen.LOGGER, "warning", lambda *args, **kwargs: warnings.append(args))

    resolved = screen.find(locator)

    assert resolved is element
    assert any("Self-healing locator used" in str(args[0]) for args in warnings)


def test_type_text_verification_reads_web_element_property_values():
    element = _Element()
    element.property_value = "Mobile QA"
    screen = BaseScreen(
        _Driver("Android"),
        settings={"retries": {"action_default": 3, "action_delay_seconds": 0}},
    )
    screen._resolve = lambda locator, timeout_ms=None: element

    screen._verify_text_entry(screen.locator("css selector", "#name", "name input"), "Mobile QA")
