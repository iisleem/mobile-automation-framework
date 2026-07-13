from __future__ import annotations

import pytest

from flows.login_flow import LoginFlow


pytestmark = [pytest.mark.smoke, pytest.mark.native]


def test_login_successfully(mobile_driver):
    LoginFlow(mobile_driver).login_successfully()
