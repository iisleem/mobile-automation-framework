from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from automation_core.reporting import ReportingFinalizeResult, finalize_allure_reporting


DEFAULT_REPORT_KIND = "core"
REPORT_KIND_CHOICES = ("core", "allure", "both", "summary")
DEFAULT_RESULTS_DIR = Path("reports") / "allure-results"
DEFAULT_OUTPUT_DIR = Path("reports") / "automation-report"
DEFAULT_HISTORY_DIR = Path("reports") / "history"
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
        enrichers=[_mobile_report_enricher(mobile_metadata["test"])],
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
    test_metadata = _without_empty(
        {
            "domain": "mobile",
            "environment": env_name,
            "profile": profile_name,
            "platform": _string_value(capabilities.get("platformName")),
            "platform_version": _string_value(capabilities.get("appium:platformVersion")),
            "device_name": _string_value(capabilities.get("appium:deviceName")),
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
