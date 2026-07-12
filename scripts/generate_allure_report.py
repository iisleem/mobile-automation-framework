from __future__ import annotations

from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.allure_cli import get_allure_cli
from utils.logger import get_logger
from utils.report_generator import generate_html_report
from utils.report_opener import open_report


LOGGER = get_logger("report")


def main() -> int:
    results_dir = PROJECT_ROOT / "reports" / "allure-results"
    output_dir = PROJECT_ROOT / "reports" / "allure-report"
    allure_executable = get_allure_cli(PROJECT_ROOT, LOGGER)
    if allure_executable:
        try:
            subprocess.run(
                [allure_executable, "generate", str(results_dir), "-o", str(output_dir), "--clean"],
                check=True,
                capture_output=True,
                text=True,
            )
            report_path = output_dir / "index.html"
        except Exception:
            report_path = generate_html_report(results_dir, output_dir)
    else:
        report_path = generate_html_report(results_dir, output_dir)

    print(report_path)
    open_report(report_path, LOGGER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
