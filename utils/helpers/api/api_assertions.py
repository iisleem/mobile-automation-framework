from __future__ import annotations

import requests


def assert_status_code(response: requests.Response, expected_status: int) -> None:
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )


def assert_json_field(response: requests.Response, dotted_path: str, expected_value) -> None:
    data = response.json()
    actual = data
    for key in dotted_path.split("."):
        actual = actual[key]
    assert actual == expected_value, f"Expected JSON field {dotted_path}={expected_value!r}, got {actual!r}"
