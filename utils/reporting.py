from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
import subprocess
from typing import Any

from automation_core.healing import add_healing_result
from automation_core.reporting import ReportingFinalizeResult, finalize_allure_reporting
from utils.healing import healing_audit_path


DEFAULT_REPORT_KIND = "core"
REPORT_KIND_CHOICES = ("core", "allure", "both", "summary")
DEFAULT_RESULTS_DIR = Path("reports") / "allure-results"
DEFAULT_OUTPUT_DIR = Path("reports") / "automation-report"
DEFAULT_HISTORY_DIR = Path("reports") / "history"
DEFAULT_HEALING_AUDIT_PATH = Path("reports") / "healing" / "events.jsonl"
PROJECT_NAME = "mobile-automation-framework"
FRAMEWORK_NAME = "pytest-appium"
MOBILE_MATRIX_DIMENSIONS = ["environment", "profile", "platform", "platform_version", "device_name", "context"]


def finalize_mobile_report(
    *,
    project_root: Path,
    results_dir: str | Path = DEFAULT_RESULTS_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    report_kind: str = DEFAULT_REPORT_KIND,
    open_report: bool = False,
    env_name: str = "",
    profile_name: str = "",
    capabilities: Mapping[str, Any] | None = None,
    settings: Mapping[str, Any] | None = None,
    history_dir: str | Path | None = DEFAULT_HISTORY_DIR,
    missing_ok: bool = True,
    logger=None,
) -> ReportingFinalizeResult:
    """Finalize mobile reporting through automation-core's shared finalizer."""

    results_path = _project_path(project_root, results_dir)
    output_path = _project_path(project_root, output_dir)
    history_path = _project_path(project_root, history_dir) if history_dir is not None else None
    mobile_metadata = build_mobile_report_metadata(
        env_name=env_name,
        profile_name=profile_name,
        capabilities=capabilities or {},
    )
    healing_path = healing_audit_path(project_root, dict(settings or {}))

    return finalize_allure_reporting(
        results_path,
        output_path,
        project_name=PROJECT_NAME,
        framework=FRAMEWORK_NAME,
        history_dir=history_path,
        open_report=open_report,
        report_kind=report_kind,
        open_target="auto",
        missing_ok=missing_ok,
        metadata=mobile_metadata["run"],
        enrichers=[
            _mobile_report_enricher(mobile_metadata["test"]),
            _healing_report_enricher(healing_path),
        ],
        matrix_dimensions=MOBILE_MATRIX_DIMENSIONS,
    )


def build_mobile_report_metadata(
    *,
    env_name: str = "",
    profile_name: str = "",
    capabilities: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    capabilities = capabilities or {}
    context = _mobile_context(profile_name, capabilities)
    platform = _string_value(capabilities.get("platformName"))
    udid = _string_value(capabilities.get("appium:udid"))
    device_name = _actual_device_name(platform=platform, udid=udid, capabilities=capabilities)
    test_metadata = _without_empty(
        {
            "domain": "mobile",
            "environment": env_name,
            "profile": profile_name,
            "platform": platform,
            "platform_version": _string_value(capabilities.get("appium:platformVersion")),
            "device_name": device_name,
            "udid": udid,
            "appium_driver": _string_only(capabilities.get("appium:automationName")),
            "browser": _string_value(capabilities.get("browserName")),
            "context": context,
        }
    )
    capability_metadata = {
        key: value
        for key, value in test_metadata.items()
        if key
        in {
            "platform",
            "platform_version",
            "device_name",
            "udid",
            "appium_driver",
            "browser",
            "context",
        }
    }
    run_metadata = dict(test_metadata)
    return {"run": run_metadata, "test": {**test_metadata, "capabilities": capability_metadata}}


def preferred_report_path(result: ReportingFinalizeResult) -> Path | None:
    if result.report_kind == "allure":
        statuses = (result.allure, result.core, result.summary)
    elif result.report_kind == "summary":
        statuses = (result.summary, result.core, result.allure)
    else:
        statuses = (result.core, result.summary, result.allure)

    for status in statuses:
        if status.generated and status.path:
            return Path(status.path)
    return None


def reporting_result_lines(result: ReportingFinalizeResult) -> list[str]:
    lines: list[str] = []
    for label, status in (("Core", result.core), ("Summary", result.summary), ("Allure", result.allure)):
        if not status.requested:
            continue
        if status.generated:
            lines.append(f"{label} report generated: {status.path}")
            if label == "Core" and getattr(status, "run_path", None):
                lines.append(f"{label} latest run details: {status.run_path}")
        else:
            detail = status.error or "; ".join(status.warnings) or status.status
            lines.append(f"{label} report {status.status}: {detail}")
    lines.extend(f"Warning: {warning}" for warning in result.warnings)
    lines.extend(f"Error: {error}" for error in result.errors)
    if result.opened_path:
        action = "Opened report" if result.opened else "Report not opened"
        lines.append(f"{action}: {result.opened_path}")
    return lines


def _mobile_report_enricher(metadata: dict[str, Any]) -> Callable[[Any], Any]:
    def enrich(report: Any) -> Any:
        for test in getattr(report, "tests", []):
            if metadata.get("domain"):
                test.domain = metadata["domain"]
            if metadata.get("profile"):
                test.profile = metadata["profile"]
            if metadata.get("environment"):
                test.environment = metadata["environment"]

            capabilities = metadata.get("capabilities", {})
            if isinstance(getattr(test, "capabilities", None), dict):
                test.capabilities.update(capabilities)
            if isinstance(getattr(test, "metadata", None), dict):
                for key, value in metadata.items():
                    if key == "capabilities":
                        continue
                    test.metadata.setdefault(key, value)
        return report

    return enrich


def _healing_report_enricher(audit_path: Path) -> Callable[[Any], Any]:
    def enrich(report: Any) -> Any:
        events = _read_healing_events(audit_path)
        if not events:
            return report
        unmatched = []
        for event in events:
            if not _attach_healing_event(report, event):
                unmatched.append(event)
        if unmatched and isinstance(getattr(report, "metadata", None), dict):
            report.metadata.setdefault("healing_events", []).extend(unmatched)
            report.metadata["healing_attempt_count"] = len(events)
        return report

    return enrich


def _actual_device_name(*, platform: str, udid: str, capabilities: Mapping[str, Any]) -> str:
    configured_name = _string_value(capabilities.get("appium:deviceName"))
    if not udid:
        return configured_name
    if platform.lower() == "ios":
        return _ios_simulator_name_for_udid(udid)
    if configured_name and configured_name == udid:
        return configured_name
    return ""


def _ios_simulator_name_for_udid(udid: str) -> str:
    try:
        completed = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "--json"],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        devices = json.loads(completed.stdout).get("devices", {})
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return ""

    for device_list in devices.values():
        if not isinstance(device_list, list):
            continue
        for device in device_list:
            if not isinstance(device, dict):
                continue
            if str(device.get("udid", "")) == udid:
                return _string_value(device.get("name"))
    return ""


def _attach_healing_event(report: Any, event: dict[str, Any]) -> bool:
    event_test_id = str(event.get("test_id") or "")
    tests = list(getattr(report, "tests", []))
    for test in tests:
        if _healing_event_matches_test(event_test_id, test):
            add_healing_result(test, _HealingResultPayload(event))
            return True
    if event_test_id:
        return False
    if len(tests) == 1:
        add_healing_result(tests[0], _HealingResultPayload(event))
        return True
    return False


def _healing_event_matches_test(event_test_id: str, test: Any) -> bool:
    if not event_test_id:
        return False
    candidates = {
        str(getattr(test, "id", "")),
        str(getattr(test, "name", "")),
        str(getattr(test, "full_name", "")),
        str(getattr(test, "fullName", "")),
    }
    normalized_event = _normalize_test_id(event_test_id)
    return any(normalized_event in _normalize_test_id(candidate) for candidate in candidates if candidate)


def _read_healing_events(audit_path: Path) -> list[dict[str, Any]]:
    if not audit_path.exists():
        return []
    events: list[dict[str, Any]] = []
    with audit_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def _normalize_test_id(value: str) -> str:
    return value.replace(".py", "").replace("::", ".").replace("/", ".").replace("\\", ".").lower()


class _HealingResultPayload:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    @property
    def applied(self) -> bool:
        return str(self._payload.get("decision", "")).lower() == "applied"

    def to_dict(self) -> dict[str, Any]:
        return self._payload


def _mobile_context(profile_name: str, capabilities: Mapping[str, Any]) -> str:
    if capabilities.get("browserName"):
        return "mobile-web"
    profile_key = profile_name.lower()
    webview_keys = {
        "appium:ensureWebviewsHavePages",
        "appium:includeSafariInWebviews",
        "appium:fullContextList",
        "appium:webviewConnectTimeout",
        "appium:additionalWebviewBundleIds",
    }
    if "hybrid" in profile_key or any(key in capabilities for key in webview_keys):
        return "webview"
    return "native"


def _project_path(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, int | float | bool):
        return str(value)
    return ""


def _string_only(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _without_empty(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in ("", None)}
