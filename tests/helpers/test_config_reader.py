from __future__ import annotations

import pytest

from conftest import PROJECT_ROOT
from utils.config_reader import ConfigReader


pytestmark = pytest.mark.helpers


def test_config_reader_load_preserves_mobile_shape():
    config = ConfigReader(PROJECT_ROOT).load("qa")

    assert config["environment"] == "qa"
    assert "environment_config" in config
    assert "base_url" not in config
    assert config["environment_config"]["api_base_url"]
    assert config["execution"]["default_profile"] == "android_the_app"


def test_config_reader_read_capabilities_uses_config_file_and_env_interpolation(monkeypatch):
    monkeypatch.setenv("IOS_PLATFORM_VERSION", "18.4")

    capabilities = ConfigReader(PROJECT_ROOT).read_capabilities()

    assert "ios_the_app" in capabilities["profiles"]
    assert capabilities["profiles"]["ios_the_app"]["appium:platformVersion"] == "18.4"
