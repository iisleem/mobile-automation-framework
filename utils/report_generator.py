from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


STATUS_ORDER = {"failed": 0, "broken": 1, "skipped": 2, "passed": 3}


def generate_html_report(results_dir: Path, output_dir: Path) -> Path:
    tests = read_allure_results(results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "index.html"
    report_path.write_text(_render_html(tests), encoding="utf-8")
    return report_path


def read_allure_results(results_dir: Path) -> list[dict[str, Any]]:
    if not results_dir.exists():
        return []

    tests: list[dict[str, Any]] = []
    for path in sorted(results_dir.glob("*-result.json")):
        with path.open("r", encoding="utf-8") as file:
            result = json.load(file)
        tests.append(
            {
                "name": result.get("name", path.stem),
                "full_name": result.get("fullName", ""),
                "status": result.get("status", "unknown"),
                "duration_ms": _duration_ms(result),
                "message": result.get("statusDetails", {}).get("message", ""),
            }
        )

    return sorted(tests, key=lambda item: (STATUS_ORDER.get(item["status"], 9), item["name"]))


def summarize_results(tests: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {status: sum(1 for test in tests if test["status"] == status) for status in STATUS_ORDER}
    total = len(tests)
    passed = counts.get("passed", 0)
    failed = counts.get("failed", 0) + counts.get("broken", 0)
    return {
        "total": total,
        "passed": passed,
        "failed": counts.get("failed", 0),
        "broken": counts.get("broken", 0),
        "skipped": counts.get("skipped", 0),
        "duration_ms": sum(test["duration_ms"] for test in tests),
        "pass_rate": round((passed / total) * 100, 2) if total else 0,
        "status": "passed" if total and not failed else "failed" if total else "unknown",
    }


def generate_device_matrix_dashboard(device_runs: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "index.html"
    report_path.write_text(_render_device_matrix_html(device_runs), encoding="utf-8")
    return report_path


def _duration_ms(result: dict[str, Any]) -> int:
    start = result.get("start", 0)
    stop = result.get("stop", start)
    return max(0, int(stop) - int(start))


def _render_html(tests: list[dict[str, Any]]) -> str:
    summary = summarize_results(tests)
    rows = "\n".join(_render_row(test) for test in tests) or "<tr><td colspan='4'>No Allure results found.</td></tr>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Mobile Test Results</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    h1 {{ margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 12px; margin: 24px 0; flex-wrap: wrap; }}
    .metric {{ border: 1px solid #d1d5db; border-radius: 6px; padding: 12px 16px; min-width: 110px; }}
    .metric strong {{ display: block; font-size: 24px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; }}
    .passed {{ color: #047857; font-weight: 700; }}
    .failed, .broken {{ color: #b91c1c; font-weight: 700; }}
    .skipped {{ color: #92400e; font-weight: 700; }}
    .message {{ color: #4b5563; white-space: pre-wrap; }}
  </style>
</head>
<body>
  <h1>Mobile Test Results</h1>
  <p>Generated from Allure JSON result files.</p>
  <section class="summary">
    <div class="metric"><strong>{summary["total"]}</strong>Total</div>
    <div class="metric"><strong>{summary["passed"]}</strong>Passed</div>
    <div class="metric"><strong>{summary["failed"]}</strong>Failed</div>
    <div class="metric"><strong>{summary["broken"]}</strong>Broken</div>
    <div class="metric"><strong>{summary["skipped"]}</strong>Skipped</div>
    <div class="metric"><strong>{summary["pass_rate"]}%</strong>Pass rate</div>
  </section>
  <table>
    <thead><tr><th>Status</th><th>Test</th><th>Duration</th><th>Message</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""


def _render_row(test: dict[str, Any]) -> str:
    status = html.escape(test["status"])
    name = html.escape(test["name"])
    full_name = html.escape(test["full_name"])
    duration = f"{test['duration_ms'] / 1000:.2f}s"
    message = html.escape(test["message"])
    return f"""<tr>
  <td class="{status}">{status}</td>
  <td><strong>{name}</strong><br>{full_name}</td>
  <td>{duration}</td>
  <td class="message">{message}</td>
</tr>"""


def _render_device_matrix_html(device_runs: list[dict[str, Any]]) -> str:
    cards = "\n".join(_render_device_card(run) for run in device_runs)
    rows = "\n".join(_render_device_row(run) for run in device_runs)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Device Matrix Dashboard</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; color: #172033; background: #f6f7f9; }}
    header {{ background: #102033; color: #ffffff; padding: 28px 36px; }}
    main {{ padding: 28px 36px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin: 24px 0; }}
    .card {{ background: #ffffff; border: 1px solid #dde3ea; border-radius: 8px; padding: 18px; }}
    .status {{ display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
    .passed {{ color: #047857; background: #dff7ed; }}
    .failed {{ color: #b91c1c; background: #fee2e2; }}
    .unknown {{ color: #4b5563; background: #e5e7eb; }}
    table {{ border-collapse: collapse; width: 100%; background: #ffffff; border: 1px solid #dde3ea; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
    th {{ background: #eef2f7; }}
    a {{ color: #1457a8; }}
  </style>
</head>
<body>
  <header>
    <h1>Device Matrix Dashboard</h1>
    <p>One pytest run per configured mobile capability profile.</p>
  </header>
  <main>
    <section class="cards">{cards}</section>
    <table>
      <thead><tr><th>Profile</th><th>Status</th><th>Total</th><th>Passed</th><th>Failed</th><th>Report</th><th>Log</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </main>
</body>
</html>
"""


def _render_device_card(run: dict[str, Any]) -> str:
    summary = run["summary"]
    status = html.escape(summary["status"])
    profile = html.escape(run["profile"])
    return f"""<article class="card">
  <h2>{profile}</h2>
  <span class="status {status}">{status}</span>
  <p>{summary["passed"]}/{summary["total"]} passed, {summary["failed"] + summary["broken"]} failed or broken.</p>
</article>"""


def _render_device_row(run: dict[str, Any]) -> str:
    summary = run["summary"]
    status = html.escape(summary["status"])
    profile = html.escape(run["profile"])
    return f"""<tr>
  <td>{profile}</td>
  <td><span class="status {status}">{status}</span></td>
  <td>{summary["total"]}</td>
  <td>{summary["passed"]}</td>
  <td>{summary["failed"] + summary["broken"]}</td>
  <td><a href="{html.escape(run["report_href"])}">Open</a></td>
  <td><a href="{html.escape(run["log_href"])}">Log</a></td>
</tr>"""
