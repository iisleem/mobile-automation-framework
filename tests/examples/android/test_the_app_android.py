from __future__ import annotations

import pytest

from flows.the_app import TheAppLoginFlow
from utils.helpers.accessibility import assert_no_unlabeled_controls
from utils.helpers.device import DeviceHelper


pytestmark = [pytest.mark.android, pytest.mark.native, pytest.mark.smoke]


def test_android_the_app_login_flow(mobile_driver):
    TheAppLoginFlow(mobile_driver).login_successfully()


def test_android_device_and_accessibility_helpers(mobile_driver):
    DeviceHelper(mobile_driver).rotate_portrait()
    assert_no_unlabeled_controls(mobile_driver.page_source, platform="android")
