from __future__ import annotations

import pytest

from flows.the_app import TheAppLoginFlow
from utils.helpers.contexts import ContextHelper
from utils.helpers.device import DeviceHelper


pytestmark = [pytest.mark.ios, pytest.mark.native, pytest.mark.smoke]


def test_ios_the_app_login_flow(mobile_driver):
    TheAppLoginFlow(mobile_driver).login_successfully()


def test_ios_device_and_context_helpers(mobile_driver):
    DeviceHelper(mobile_driver).rotate_portrait()
    contexts = ContextHelper(mobile_driver).contexts()
    assert "NATIVE_APP" in contexts
