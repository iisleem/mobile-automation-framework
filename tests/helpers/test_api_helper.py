from __future__ import annotations

import json

import pytest
import requests

from utils.helpers.api import assert_json_field, assert_status_code


pytestmark = pytest.mark.helpers


def test_api_assertions_with_synthetic_response():
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps({"user": {"id": 7}}).encode("utf-8")

    assert_status_code(response, 200)
    assert_json_field(response, "user.id", 7)
