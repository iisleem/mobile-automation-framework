from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.config_reader import ConfigReader
from utils.logger import get_logger
from utils.reporting import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_KIND,
    DEFAULT_RESULTS_DIR,
    REPORT_KIND_CHOICES,
    finalize_mobile_report,
    preferred_report_path,
    reporting_result_lines,
)


LOGGER = get_logger("report")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate mobile reports from Allure result files.")
    parser.add_argument("--results", default=str(DEFAULT_RESULTS_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--report-kind",
        choices=REPORT_KIND_CHOICES,
        default=DEFAULT_REPORT_KIND,
        help="Report kind: core, allure, both, or summary. Defaults to core.",
    )
    parser.add_argument("--env", default="qa")
    parser.add_argument("--profile", help="Capability profile metadata for the generated report.")
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args(argv)

    profile_name = args.profile or ConfigReader(PROJECT_ROOT).read_settings()["execution"]["default_profile"]
    result = finalize_mobile_report(
        project_root=PROJECT_ROOT,
        results_dir=args.results,
        output_dir=args.output,
        report_kind=args.report_kind,
        open_report=not args.no_open,
        env_name=args.env,
        profile_name=profile_name,
        capabilities=_report_capabilities(profile_name),
        logger=LOGGER,
    )
    for line in reporting_result_lines(result):
        print(line)
    report_path = preferred_report_path(result)
    if report_path:
        print(report_path)
    return 0 if result.ok else 1


def _report_capabilities(profile_name: str) -> dict:
    from utils.capabilities import resolve_capabilities

    capabilities_config = ConfigReader(PROJECT_ROOT).read_capabilities()
    try:
        return resolve_capabilities(PROJECT_ROOT, capabilities_config, profile_name)
    except Exception as error:
        LOGGER.warning("Could not resolve mobile report metadata for profile %s: %s", profile_name, error)
        return capabilities_config.get("profiles", {}).get(profile_name, {})


if __name__ == "__main__":
    raise SystemExit(main())
