from __future__ import annotations

from typing import Any

import requests


def create_mobile_driver(
    server_url: str,
    capabilities: dict[str, Any],
):
    from appium import webdriver

    options = build_appium_options(capabilities)
    return webdriver.Remote(command_executor=server_url, options=options)


def build_appium_options(capabilities: dict[str, Any]):
    option_class = _resolve_option_class(capabilities)
    options = option_class()
    for key, value in capabilities.items():
        options.set_capability(key, value)
    return options


def is_appium_server_ready(server_url: str, timeout_seconds: float = 2.0) -> bool:
    try:
        response = requests.get(f"{server_url.rstrip('/')}/status", timeout=timeout_seconds)
        return response.status_code < 500
    except requests.RequestException:
        return False


def describe_capabilities(capabilities: dict[str, Any]) -> str:
    safe_capabilities = {key: ("***" if _looks_secret(key) else value) for key, value in sorted(capabilities.items())}
    return "\n".join(f"{key}: {value}" for key, value in safe_capabilities.items())


def _resolve_option_class(capabilities: dict[str, Any]):
    platform_name = str(capabilities.get("platformName", "")).lower()
    automation_name = str(capabilities.get("appium:automationName", capabilities.get("automationName", ""))).lower()

    if platform_name == "android" and automation_name == "uiautomator2":
        try:
            from appium.options.android import UiAutomator2Options
        except ImportError:
            from appium.options.android.uiautomator2 import UiAutomator2Options

        return UiAutomator2Options

    if platform_name == "ios" and automation_name == "xcuitest":
        try:
            from appium.options.ios import XCUITestOptions
        except ImportError:
            from appium.options.ios.xcuitest import XCUITestOptions

        return XCUITestOptions

    from appium.options.common import AppiumOptions

    return AppiumOptions


def _looks_secret(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ("password", "token", "secret", "key"))
