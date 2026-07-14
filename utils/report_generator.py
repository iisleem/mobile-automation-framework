from __future__ import annotations

from pathlib import Path
from typing import Any

from automation_core.reporting import (
    generate_device_matrix_dashboard as core_generate_device_matrix_dashboard,
    generate_html_report as core_generate_html_report,
    read_allure_results as core_read_allure_results,
    summarize_results as core_summarize_results,
)

__all__ = [
    "generate_device_matrix_dashboard",
    "generate_html_report",
    "read_allure_results",
    "summarize_results",
]


def generate_html_report(results_dir: Path, output_dir: Path) -> Path:
    return core_generate_html_report(
        results_dir,
        output_dir,
        title="Mobile Test Results",
        description="Generated from Allure JSON result files.",
    )


def generate_device_matrix_dashboard(device_runs: list[dict[str, Any]], output_dir: Path) -> Path:
    return core_generate_device_matrix_dashboard(device_runs, output_dir)


def read_allure_results(results_dir: Path) -> list[dict[str, Any]]:
    return core_read_allure_results(results_dir, missing_ok=True)


def summarize_results(tests: list[dict[str, Any]]) -> dict[str, Any]:
    return core_summarize_results(tests)
