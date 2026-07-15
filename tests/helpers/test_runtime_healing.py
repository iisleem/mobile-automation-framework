from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from conftest import PROJECT_ROOT
from screens.base_screen import BaseScreen
from utils.config_reader import ConfigReader
from utils.healing import discover_mobile_candidates, runtime_healing_enabled
from utils.reporting import _healing_report_enricher


pytestmark = pytest.mark.helpers


class _HealingDriver:
    def __init__(self, source: str, platform_name: str = "Android", context: str = "NATIVE_APP") -> None:
        self.capabilities = {"platformName": platform_name}
        self.page_source = source
        self.current_context = context

    def find_elements(self, by: str, value: str):
        return []


class _Element:
    pass


def test_runtime_healing_config_defaults_disabled():
    settings = ConfigReader(PROJECT_ROOT).read_settings()

    assert settings["runtime_healing"]["mode"] == "disabled"
    assert runtime_healing_enabled(settings) is False


def test_runtime_healing_suggest_records_but_does_not_apply(tmp_path):
    driver = _HealingDriver(_native_source(content_desc="loginBtn"))
    screen = BaseScreen(driver, settings=_settings(tmp_path, mode="suggest", min_score=0.1))
    calls: list[str] = []

    def wait_for(locator, timeout_ms):
        calls.append(locator.value)
        raise TimeoutException("missing")

    screen._wait_for = wait_for

    with pytest.raises(TimeoutException, match="decision=suggested"):
        screen._resolve(screen.accessibility_id("oldLogin", "Login button"), action_name="tap")

    assert calls == ["oldLogin"]
    event = _read_audit_event(tmp_path)
    assert event["decision"] == "suggested"
    assert event["selected"]["candidate"]["value"] == "loginBtn"


def test_runtime_healing_apply_uses_candidate_when_core_approves(tmp_path):
    element = _Element()
    driver = _HealingDriver(_native_source(content_desc="loginBtn"))
    screen = BaseScreen(driver, settings=_settings(tmp_path, mode="apply", min_score=0.1))
    calls: list[tuple[str, str]] = []

    def wait_for(locator, timeout_ms):
        calls.append((locator.by, locator.value))
        if locator.value == "oldLogin":
            raise TimeoutException("missing")
        return element

    screen._wait_for = wait_for

    resolved = screen._resolve(screen.accessibility_id("oldLogin", "Login button"), action_name="tap")

    assert resolved is element
    assert (AppiumBy.ACCESSIBILITY_ID, "loginBtn") in calls
    event = _read_audit_event(tmp_path)
    assert event["decision"] == "applied"


def test_runtime_healing_ambiguous_candidate_fails_clearly(tmp_path):
    source = (
        "<hierarchy>"
        + _node(content_desc="loginBtn", text="Login")
        + _node(content_desc="loginBtn", text="Login")
        + "</hierarchy>"
    )
    driver = _HealingDriver(source)
    screen = BaseScreen(driver, settings=_settings(tmp_path, mode="apply", min_score=0.1))
    screen._wait_for = lambda locator, timeout_ms: (_ for _ in ()).throw(TimeoutException("missing"))

    with pytest.raises(TimeoutException, match="decision=rejected"):
        screen._resolve(screen.accessibility_id("oldLogin", "Login button"), action_name="tap")

    event = _read_audit_event(tmp_path)
    assert event["decision"] == "rejected"
    assert "no viable" in event["reason"]


def test_native_source_candidate_extraction_uses_mobile_signals():
    driver = _HealingDriver(_native_source(content_desc="loginBtn", resource_id="com.example:id/login", text="Login"))
    original = SimpleNamespace(by=AppiumBy.ACCESSIBILITY_ID, value="oldLogin", description="Login button")

    candidates = discover_mobile_candidates(driver, original, action="tap", max_candidates=10)

    values = {candidate.value for candidate in candidates}
    assert "loginBtn" in values
    assert "com.example:id/login" in values
    assert any(candidate.descriptor.source == "native-page-source" for candidate in candidates)
    assert all(candidate.descriptor.metadata["context"] == "NATIVE_APP" for candidate in candidates)


def test_healing_report_enricher_uses_core_add_result(tmp_path):
    audit_path = tmp_path / "reports" / "healing" / "events.jsonl"
    audit_path.parent.mkdir(parents=True)
    audit_path.write_text(
        json.dumps(
            {
                "decision": "applied",
                "test_id": "tests/helpers/test_runtime_healing.py::test_example",
                "reason": "selected candidate score 0.90 met safety gates",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    test = SimpleNamespace(
        id="",
        name="test_example",
        full_name="tests.helpers.test_runtime_healing.test_example",
        metadata={},
    )
    report = SimpleNamespace(tests=[test], metadata={})

    _healing_report_enricher(audit_path)(report)

    assert test.metadata["healing_attempt_count"] == 1
    assert test.metadata["healing_applied_count"] == 1
    assert test.metadata["healing_events"][0]["decision"] == "applied"


def _settings(tmp_path, *, mode: str, min_score: float) -> dict:
    return {
        "timeouts": {"default_timeout_ms": 1000, "short_timeout_ms": 100},
        "self_healing": {"enabled": False, "timeout_ms": 100},
        "runtime_healing": {
            "mode": mode,
            "min_score": min_score,
            "ambiguity_delta": 0.05,
            "max_candidates": 10,
            "allowed_actions": ["tap", "type_text", "type_text_with_keyboard", "find"],
            "audit_path": str(tmp_path / "reports" / "healing" / "events.jsonl"),
        },
    }


def _read_audit_event(tmp_path) -> dict:
    audit_path = tmp_path / "reports" / "healing" / "events.jsonl"
    return json.loads(audit_path.read_text(encoding="utf-8").splitlines()[-1])


def _native_source(*, content_desc: str = "", resource_id: str = "", text: str = "") -> str:
    return f"<hierarchy>{_node(content_desc=content_desc, resource_id=resource_id, text=text)}</hierarchy>"


def _node(*, content_desc: str = "", resource_id: str = "", text: str = "") -> str:
    return (
        '<node class="android.widget.Button" clickable="true" enabled="true" '
        f'text="{text}" content-desc="{content_desc}" resource-id="{resource_id}" />'
    )
