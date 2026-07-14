from __future__ import annotations

import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import WebDriverException


# Keep this list non-destructive. In particular, do not click Android ANR
# "Close app"; leaving a real crash visible is safer than hiding it.
ANDROID_SYSTEM_DIALOG_BUTTONS = ("Wait", "OK", "Got it", "Continue")
ANDROID_SYSTEM_DIALOG_PACKAGES = {
    "android",
    "com.android.permissioncontroller",
    "com.android.systemui",
    "com.google.android.permissioncontroller",
}


def dismiss_android_system_dialogs(
    driver,
    logger=None,
    timeout_seconds: float = 0.0,
    poll_interval_seconds: float = 0.2,
) -> bool:
    """Dismiss Android system overlays that can block sample app interactions."""

    if str(driver.capabilities.get("platformName", "")).lower() != "android":
        return False
    if not hasattr(driver, "find_elements"):
        return False

    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while True:
        if _dismiss_android_dialog_once(driver, logger):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(max(0.0, poll_interval_seconds))


def _dismiss_android_dialog_once(driver, logger=None) -> bool:
    for button_text in ANDROID_SYSTEM_DIALOG_BUTTONS:
        selector = f'new UiSelector().clickable(true).text("{button_text}")'
        try:
            buttons = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
        except WebDriverException:
            continue

        for button in buttons:
            if not _is_android_system_dialog_button(button):
                continue
            try:
                button.click()
            except WebDriverException:
                continue
            if logger:
                logger.warning("Dismissed Android system dialog button: %s", button_text)
            return True
    return False


def _is_android_system_dialog_button(button) -> bool:
    try:
        package_name = button.get_attribute("package")
    except WebDriverException:
        return False
    return package_name in ANDROID_SYSTEM_DIALOG_PACKAGES
