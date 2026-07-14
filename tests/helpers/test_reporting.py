from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

import framework
from utils import reporting


pytestmark = pytest.mark.helpers


def test_mobile_report_metadata_is_serializable_and_mobile_specific():
    metadata = reporting.build_mobile_report_metadata(
        env_name="qa",
        profile_name="android_mobile_web",
        capabilities={
            "platformName": "Android",
            "browserName": "Chrome",
            "appium:deviceName": "Android Emulator",
            "appium:platformVersion": 15,
            "appium:automationName": object(),
        },
    )

    json.dumps(metadata)

    assert metadata["run"]["domain"] == "mobile"
    assert metadata["run"]["profile"] == "android_mobile_web"
    assert metadata["run"]["platform"] == "Android"
    assert metadata["run"]["platform_version"] == "15"
    assert metadata["run"]["device_name"] == "Android Emulator"
    assert metadata["run"]["browser"] == "Chrome"
    assert metadata["run"]["context"] == "mobile-web"
    assert "appium_driver" not in metadata["run"]


def test_finalize_mobile_report_uses_core_finalizer_and_enriches_tests(monkeypatch, tmp_path):
    captured: dict = {}
    expected = SimpleNamespace(
        report_kind="both",
        core=_status(
            requested=True, generated=True, path=str(tmp_path / "reports" / "automation-report" / "index.html")
        ),
        summary=_status(),
        allure=_status(requested=True, generated=False, status="missing_cli"),
        warnings=["Official Allure CLI was not found; core reporting remains available."],
        errors=[],
        opened=False,
        opened_path=None,
        ok=True,
    )

    def fake_finalize(results_dir, output_dir, **kwargs):
        captured["results_dir"] = results_dir
        captured["output_dir"] = output_dir
        captured["kwargs"] = kwargs
        report = SimpleNamespace(
            tests=[
                SimpleNamespace(
                    domain="",
                    profile="",
                    environment="",
                    capabilities={},
                    metadata={},
                )
            ]
        )
        for enricher in kwargs["enrichers"]:
            enricher(report)
        captured["test"] = report.tests[0]
        return expected

    monkeypatch.setattr(reporting, "finalize_allure_reporting", fake_finalize)

    result = reporting.finalize_mobile_report(
        project_root=tmp_path,
        report_kind="both",
        open_report=True,
        env_name="qa",
        profile_name="ios_hybrid_demo",
        capabilities={
            "platformName": "iOS",
            "appium:deviceName": "iPhone 15",
            "appium:platformVersion": "18.0",
            "appium:automationName": "XCUITest",
            "appium:includeSafariInWebviews": True,
        },
    )

    assert result is expected
    assert captured["results_dir"] == tmp_path / "reports" / "allure-results"
    assert captured["output_dir"] == tmp_path / "reports" / "automation-report"
    assert captured["kwargs"]["report_kind"] == "both"
    assert captured["kwargs"]["open_report"] is True
    assert captured["kwargs"]["metadata"]["domain"] == "mobile"
    assert captured["kwargs"]["matrix_dimensions"] == reporting.MOBILE_MATRIX_DIMENSIONS
    assert captured["test"].domain == "mobile"
    assert captured["test"].profile == "ios_hybrid_demo"
    assert captured["test"].environment == "qa"
    assert captured["test"].capabilities["appium_driver"] == "XCUITest"
    assert captured["test"].metadata["context"] == "webview"


def test_report_open_auto_uses_product_report_not_official_allure(monkeypatch, tmp_path):
    product_report = tmp_path / "reports" / "automation-report" / "index.html"
    official_allure = tmp_path / "reports" / "automation-report" / "allure" / "index.html"
    product_report.parent.mkdir(parents=True)
    official_allure.parent.mkdir(parents=True)
    product_report.write_text("core", encoding="utf-8")
    official_allure.write_text("allure", encoding="utf-8")
    monkeypatch.setattr(framework, "PROJECT_ROOT", tmp_path)

    assert framework._find_report("auto") == product_report
    assert framework._find_report("allure") == official_allure


def _status(requested=False, generated=False, path=None, status="not_requested"):
    return SimpleNamespace(
        requested=requested,
        generated=generated,
        path=path,
        status=status,
        error="",
        warnings=[],
    )
