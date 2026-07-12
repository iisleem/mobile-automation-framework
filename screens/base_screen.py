from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Iterable

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.config_reader import ConfigReader
from utils.helpers.allure_debug import step
from utils.helpers.gestures import GestureHelper
from utils.logger import get_logger


LOGGER = get_logger("screen")


@dataclass(frozen=True)
class MobileLocator:
    by: str
    value: str
    description: str


@dataclass(frozen=True)
class MobileLocatorGroup:
    description: str
    candidates: tuple[MobileLocator, ...]


class BaseScreen:
    def __init__(self, driver, settings: dict | None = None) -> None:
        self.driver = driver
        self.settings = settings or ConfigReader(self.project_path()).read_settings()
        self.gestures = GestureHelper(driver)

    def locator(self, by: str, value: str, description: str) -> MobileLocator:
        return MobileLocator(by=by, value=value, description=description)

    def accessibility_id(self, value: str, description: str) -> MobileLocator:
        return self.locator(AppiumBy.ACCESSIBILITY_ID, value, description)

    def android_text(self, value: str, description: str) -> MobileLocator:
        selector = f'new UiSelector().text("{value}")'
        return self.locator(AppiumBy.ANDROID_UIAUTOMATOR, selector, description)

    def ios_predicate(self, value: str, description: str) -> MobileLocator:
        return self.locator(AppiumBy.IOS_PREDICATE, value, description)

    def locator_with_fallbacks(
        self,
        description: str,
        primary: MobileLocator | tuple[str, str],
        *fallbacks: MobileLocator | tuple[str, str],
    ) -> MobileLocatorGroup:
        candidates = tuple(
            self._as_mobile_locator(candidate, description, index)
            for index, candidate in enumerate((primary, *fallbacks))
        )
        return MobileLocatorGroup(description=description, candidates=candidates)

    def find(self, locator: MobileLocator | MobileLocatorGroup, timeout_ms: int | None = None):
        return self._resolve(locator, timeout_ms=timeout_ms)

    def find_all(self, locator: MobileLocator, timeout_ms: int | None = None):
        self.find(locator, timeout_ms=timeout_ms)
        return self.driver.find_elements(locator.by, locator.value)

    def tap(
        self,
        locator: MobileLocator | MobileLocatorGroup,
        description: str | None = None,
        verify: Callable[[], object] | MobileLocator | MobileLocatorGroup | None = None,
    ) -> None:
        action_name = f"Tap {description or self._description(locator)}"

        def action() -> None:
            resolved = self._resolve(locator)
            resolved.click()
            self._verify_action_result(action_name, verify)

        with step(action_name):
            self._run_mobile_action(action_name, action)

    def type_text(
        self,
        locator: MobileLocator | MobileLocatorGroup,
        value: str,
        clear_first: bool = True,
        description: str | None = None,
        sensitive: bool = False,
    ) -> None:
        action_name = f"Type into {description or self._description(locator)}"

        def action() -> None:
            if self._is_ios():
                self._configure_ios_keyboard()
            element = self._resolve(locator)
            try:
                element.click()
            except WebDriverException:
                pass
            if clear_first:
                element.clear()
            element.send_keys(value)
            self._verify_text_entry(locator, value, sensitive=sensitive)

        with step(action_name):
            self._run_mobile_action(action_name, action)

    def type_text_with_keyboard(
        self,
        locator: MobileLocator | MobileLocatorGroup,
        value: str,
        clear_first: bool = True,
        description: str | None = None,
        sensitive: bool = False,
    ) -> None:
        action_name = f"Type with keyboard into {description or self._description(locator)}"

        def action() -> None:
            element = self._resolve(locator)
            if self._is_ios():
                self._configure_ios_keyboard()
                element.click()
                if clear_first:
                    element.clear()
                self.driver.execute_script("mobile: keys", {"keys": list(value)})
                self._verify_text_entry(locator, value, sensitive=sensitive)
                return

            element.click()
            if clear_first:
                element.clear()
            element.send_keys(value)
            self._verify_text_entry(locator, value, sensitive=sensitive)

        with step(action_name):
            self._run_mobile_action(action_name, action)

    def text(self, locator: MobileLocator | MobileLocatorGroup) -> str:
        element = self._resolve(locator)
        return element.text

    def expect_visible(self, locator: MobileLocator | MobileLocatorGroup, description: str | None = None) -> None:
        with step(f"Verify {description or self._description(locator)} is visible"):
            self._resolve(locator)

    def expect_text_contains(self, locator: MobileLocator | MobileLocatorGroup, expected_text: str) -> None:
        actual_text = self.text(locator)
        assert expected_text in actual_text, f"Expected {actual_text!r} to contain {expected_text!r}"

    def source_contains(self, expected_text: str) -> bool:
        return expected_text in self.driver.page_source

    def assert_source_contains(self, expected_text: str) -> None:
        assert self.source_contains(expected_text), f"Expected page source to contain {expected_text!r}"

    def scroll_until_visible(
        self,
        locator: MobileLocator | MobileLocatorGroup,
        max_scrolls: int = 5,
    ):
        last_error: Exception | None = None
        for _ in range(max_scrolls + 1):
            try:
                return self._resolve(locator, timeout_ms=self._short_timeout_ms())
            except Exception as error:
                last_error = error
                self.gestures.scroll_down()
        raise AssertionError(f"Could not find {self._description(locator)} after scrolling") from last_error

    def hide_keyboard(self) -> None:
        try:
            self.driver.hide_keyboard()
        except WebDriverException:
            return

    def _resolve(self, locator: MobileLocator | MobileLocatorGroup, timeout_ms: int | None = None):
        raw_candidates = locator.candidates if isinstance(locator, MobileLocatorGroup) else (locator,)
        candidates = self._supported_locators(raw_candidates)
        enabled = bool(self.settings.get("self_healing", {}).get("enabled", False))
        timeout = timeout_ms or self._default_timeout_ms()

        if not candidates:
            raise TimeoutException(f"No supported locators for platform: {self._description(locator)}")

        if not enabled:
            return self._wait_for(candidates[0], timeout)

        first_error: Exception | None = None
        for index, candidate in enumerate(candidates):
            try:
                element = self._wait_for(candidate, timeout if index == 0 else self._healing_timeout_ms())
                if index > 0:
                    LOGGER.warning(
                        "Self-healing locator used for '%s'. Fallback: %s=%s",
                        self._description(locator),
                        candidate.by,
                        candidate.value,
                    )
                return element
            except TimeoutException as error:
                if first_error is None:
                    first_error = error
                continue
        raise first_error or TimeoutException(f"Unable to resolve locator: {locator}")

    def _wait_for(self, locator: MobileLocator, timeout_ms: int):
        wait = WebDriverWait(self.driver, timeout_ms / 1000)
        return wait.until(EC.visibility_of_element_located((locator.by, locator.value)))

    def _as_mobile_locator(
        self,
        candidate: MobileLocator | tuple[str, str],
        description: str,
        index: int,
    ) -> MobileLocator:
        if isinstance(candidate, MobileLocator):
            return candidate
        by, value = candidate
        suffix = "primary" if index == 0 else f"fallback {index}"
        return MobileLocator(by=by, value=value, description=f"{description} {suffix}")

    def _description(self, locator: MobileLocator | MobileLocatorGroup) -> str:
        if isinstance(locator, MobileLocatorGroup):
            return locator.description
        return locator.description

    def _default_timeout_ms(self) -> int:
        return int(self.settings.get("timeouts", {}).get("default_timeout_ms", 10000))

    def _short_timeout_ms(self) -> int:
        return int(self.settings.get("timeouts", {}).get("short_timeout_ms", 2500))

    def _healing_timeout_ms(self) -> int:
        return int(self.settings.get("self_healing", {}).get("timeout_ms", 1500))

    def _run_mobile_action(self, action_name: str, action: Callable[[], object]) -> object:
        attempts = self._action_retry_count()
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return action()
            except (AssertionError, TimeoutException, WebDriverException) as error:
                last_error = error
                if attempt >= attempts:
                    break
                LOGGER.warning(
                    "%s failed on attempt %s/%s. Retrying. Reason: %s",
                    action_name,
                    attempt,
                    attempts,
                    error,
                )
                time.sleep(self._action_retry_delay_seconds())

        raise AssertionError(f"{action_name} failed after {attempts} attempts: {last_error}") from last_error

    def _verify_action_result(
        self,
        action_name: str,
        verify: Callable[[], object] | MobileLocator | MobileLocatorGroup | None,
    ) -> None:
        if verify is None:
            return
        if isinstance(verify, (MobileLocator, MobileLocatorGroup)):
            try:
                self._resolve(verify, timeout_ms=self._default_timeout_ms())
            except TimeoutException as error:
                raise AssertionError(
                    f"Post-action verification failed for {action_name}: "
                    f"{self._description(verify)} was not visible"
                ) from error
            return
        result = verify()
        if result is False:
            raise AssertionError(f"Verification returned False for {action_name}")

    def _verify_text_entry(
        self,
        locator: MobileLocator | MobileLocatorGroup,
        expected_value: str,
        sensitive: bool = False,
    ) -> None:
        element = self._resolve(locator, timeout_ms=self._short_timeout_ms())
        observed_values = self._element_text_values(element)
        if any(self._text_value_matches(value, expected_value) for value in observed_values):
            return
        if sensitive and any(self._masked_value_matches(value, expected_value) for value in observed_values):
            return

        label = "[sensitive value]" if sensitive else repr(expected_value)
        observed = "[masked/empty]" if sensitive else repr(observed_values)
        raise AssertionError(f"Expected {self._description(locator)} to contain {label}. Observed: {observed}")

    def _element_text_values(self, element) -> tuple[str, ...]:
        values: list[str] = []
        for attribute in ("value", "text"):
            try:
                value = element.get_attribute(attribute)
            except WebDriverException:
                continue
            if value:
                values.append(str(value))
        for property_name in ("value", "textContent", "innerText"):
            getter = getattr(element, "get_property", None)
            if getter is None:
                continue
            try:
                value = getter(property_name)
            except WebDriverException:
                continue
            if value:
                values.append(str(value))
        execute_script = getattr(self.driver, "execute_script", None)
        if execute_script is not None:
            for script in (
                "return arguments[0].value",
                "return arguments[0].textContent",
                "return arguments[0].innerText",
            ):
                try:
                    value = execute_script(script, element)
                except WebDriverException:
                    continue
                if value:
                    values.append(str(value))
        try:
            text = element.text
        except WebDriverException:
            text = None
        if text:
            values.append(str(text))
        return tuple(dict.fromkeys(values))

    def _text_value_matches(self, actual_value: str, expected_value: str) -> bool:
        return actual_value == expected_value or expected_value in actual_value

    def _masked_value_matches(self, actual_value: str, expected_value: str) -> bool:
        stripped = actual_value.strip()
        if not stripped:
            return False
        mask_characters = {"*", "•", "●", "·", "∙"}
        return set(stripped) <= mask_characters and len(stripped) >= len(expected_value)

    def _action_retry_count(self) -> int:
        return max(1, int(self.settings.get("retries", {}).get("action_default", 3)))

    def _action_retry_delay_seconds(self) -> float:
        return max(0.0, float(self.settings.get("retries", {}).get("action_delay_seconds", 0.3)))

    def _supported_locators(self, candidates: Iterable[MobileLocator]) -> tuple[MobileLocator, ...]:
        platform_name = str(self.driver.capabilities.get("platformName", "")).lower()
        supported = []
        for candidate in candidates:
            if platform_name == "android" and candidate.by in {AppiumBy.IOS_PREDICATE, AppiumBy.IOS_CLASS_CHAIN}:
                continue
            if platform_name == "ios" and candidate.by == AppiumBy.ANDROID_UIAUTOMATOR:
                continue
            supported.append(candidate)
        return tuple(supported)

    def _is_ios(self) -> bool:
        return str(self.driver.capabilities.get("platformName", "")).lower() == "ios"

    def _configure_ios_keyboard(self) -> None:
        self.driver.execute_script(
            "mobile: configureLocalization",
            {
                "keyboard": {"name": "en_US", "layout": "QWERTY"},
                "language": {"name": "en"},
                "locale": {"name": "en_US"},
            },
        )

    @staticmethod
    def project_path(*parts: str) -> Path:
        return Path(__file__).resolve().parents[1].joinpath(*parts)
