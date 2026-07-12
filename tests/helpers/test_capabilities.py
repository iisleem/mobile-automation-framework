from __future__ import annotations

from pathlib import Path

import pytest

from utils.capabilities import available_profiles, resolve_capabilities
from utils.config_reader import ConfigReader


PROJECT_ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.helpers


def test_capability_profiles_load_and_resolve_local_app_path():
    config = ConfigReader(PROJECT_ROOT).read_capabilities()
    assert "android_the_app" in available_profiles(config)
    capabilities = resolve_capabilities(PROJECT_ROOT, config, "android_the_app")
    assert capabilities["platformName"] == "Android"
    assert capabilities["appium:app"].endswith("apps/TheApp.apk")
    assert Path(capabilities["appium:app"]).is_absolute()


def test_capability_cli_overrides_are_applied():
    config = ConfigReader(PROJECT_ROOT).read_capabilities()
    capabilities = resolve_capabilities(
        PROJECT_ROOT,
        config,
        "ios_the_app",
        overrides={"device_name": "iPhone 16", "platform_version": "18.0", "no_reset": True},
    )
    assert capabilities["appium:deviceName"] == "iPhone 16"
    assert capabilities["appium:platformVersion"] == "18.0"
    assert capabilities["appium:noReset"] is True


def test_mobile_web_profiles_use_appium_browser_capabilities():
    config = ConfigReader(PROJECT_ROOT).read_capabilities()

    android = resolve_capabilities(PROJECT_ROOT, config, "android_mobile_web")
    ios = resolve_capabilities(PROJECT_ROOT, config, "ios_mobile_web")

    assert android["platformName"] == "Android"
    assert android["browserName"] == "Chrome"
    assert "appium:app" not in android
    assert ios["platformName"] == "iOS"
    assert ios["browserName"] == "Safari"
    assert "appium:app" not in ios
