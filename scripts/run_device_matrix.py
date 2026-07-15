from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import shutil
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.capabilities import resolve_capabilities
from utils.config_reader import ConfigReader
from utils.logger import get_logger
from utils.report_generator import (
    generate_device_matrix_dashboard,
    read_allure_results,
    summarize_results,
)
from utils.report_opener import open_report
from utils.reporting import (
    DEFAULT_REPORT_KIND,
    REPORT_KIND_CHOICES,
    finalize_mobile_report,
    preferred_report_path,
    reporting_result_lines,
)


LOGGER = get_logger("device-matrix")


def main() -> int:
    args, extra_pytest_args = _parse_args()
    settings = ConfigReader(PROJECT_ROOT).read_settings()
    profiles = args.profiles or settings.get("execution", {}).get("profiles", [])
    profile_workers = min(
        args.profile_workers or settings.get("execution", {}).get("profile_workers", 1),
        len(profiles),
    )

    matrix_dir = PROJECT_ROOT / "reports" / "device-matrix"
    results_root = matrix_dir / "results"
    reports_root = matrix_dir / "reports"
    logs_root = matrix_dir / "logs"
    _prepare_matrix_dirs(results_root, reports_root, logs_root, args.no_generate_report)

    pytest_runs = _run_pytest_profile_matrix(
        profiles,
        profile_workers,
        args,
        extra_pytest_args,
        results_root,
        logs_root,
    )
    exit_code = max((run["exit_code"] for run in pytest_runs), default=0)
    if args.no_generate_report:
        return exit_code

    profile_runs = []
    for pytest_run in pytest_runs:
        profile = pytest_run["profile"]
        results_dir = pytest_run["results_dir"]
        report_dir = reports_root / profile
        report_path = _generate_profile_report(args, profile, results_dir, report_dir)
        tests = read_allure_results(results_dir)
        summary = summarize_results(tests)
        if pytest_run["exit_code"] and summary["status"] == "passed":
            summary["status"] = "failed"
        profile_runs.append(
            {
                "profile": profile,
                "exit_code": pytest_run["exit_code"],
                "summary": summary,
                "report_path": report_path,
                "report_href": f"reports/{profile}/index.html",
                "log_href": f"logs/{profile}.log",
            }
        )

    dashboard_path = generate_device_matrix_dashboard(profile_runs, matrix_dir)
    LOGGER.info("Generated device matrix dashboard: %s", dashboard_path)
    if not args.no_open_report:
        open_report(dashboard_path, LOGGER)
    return exit_code


def _parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description="Run pytest once per mobile capability profile.")
    parser.add_argument("--profiles", nargs="+", help="Capability profiles to run.")
    parser.add_argument("--env", default="qa")
    parser.add_argument("--profile-workers", type=int)
    parser.add_argument("--appium-server")
    parser.add_argument("--device-name")
    parser.add_argument("--platform-version")
    parser.add_argument("--udid")
    parser.add_argument("--app")
    parser.add_argument("--no-reset", action="store_true", default=None)
    parser.add_argument("--full-reset", action="store_true")
    parser.add_argument("-m", "--markers")
    parser.add_argument("-n", "--parallel-workers")
    parser.add_argument("--reruns")
    parser.add_argument("--reruns-delay")
    parser.add_argument("--report-kind", choices=REPORT_KIND_CHOICES, default=DEFAULT_REPORT_KIND)
    parser.add_argument("--no-open-report", action="store_true")
    parser.add_argument("--no-generate-report", action="store_true")
    return parser.parse_known_args()


def _prepare_matrix_dirs(
    results_root: Path,
    reports_root: Path,
    logs_root: Path,
    no_generate_report: bool,
) -> None:
    for path in (results_root, logs_root):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    if not no_generate_report:
        if reports_root.exists():
            shutil.rmtree(reports_root)
        reports_root.mkdir(parents=True, exist_ok=True)


def _run_pytest_profile_matrix(
    profiles: list[str],
    profile_workers: int,
    args: argparse.Namespace,
    extra_pytest_args: list[str],
    results_root: Path,
    logs_root: Path,
) -> list[dict]:
    if profile_workers <= 1:
        return [
            _run_pytest_for_profile(
                profile, args, extra_pytest_args, results_root / profile, logs_root / f"{profile}.log"
            )
            for profile in profiles
        ]

    results_by_profile: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=profile_workers) as executor:
        futures = {
            executor.submit(
                _run_pytest_for_profile,
                profile,
                args,
                extra_pytest_args,
                results_root / profile,
                logs_root / f"{profile}.log",
            ): profile
            for profile in profiles
        }
        for future in as_completed(futures):
            profile = futures[future]
            results_by_profile[profile] = future.result()
    return [results_by_profile[profile] for profile in profiles]


def _run_pytest_for_profile(
    profile: str,
    args: argparse.Namespace,
    extra_pytest_args: list[str],
    results_dir: Path,
    log_path: Path,
) -> dict:
    results_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pytest",
        "--env",
        args.env,
        "--profile",
        profile,
        f"--alluredir={results_dir}",
        "--no-generate-report",
    ]
    _append_optional(command, "--appium-server", args.appium_server)
    _append_optional(command, "--device-name", args.device_name)
    _append_optional(command, "--platform-version", args.platform_version)
    _append_optional(command, "--udid", args.udid)
    _append_optional(command, "--app", args.app)
    if args.no_reset:
        command.append("--no-reset")
    if args.full_reset:
        command.append("--full-reset")
    if args.markers:
        command.extend(["-m", args.markers])
    if args.parallel_workers:
        command.extend(["-n", str(args.parallel_workers)])
    reruns = args.reruns if args.reruns is not None else _retry_setting("default", 0)
    reruns_delay = args.reruns_delay if args.reruns_delay is not None else _retry_setting("delay_seconds", 0)
    if int(reruns):
        command.extend(["--reruns", str(reruns)])
    if float(reruns_delay):
        command.extend(["--reruns-delay", str(reruns_delay)])
    command.extend(_normalize_passthrough_args(extra_pytest_args))

    LOGGER.info("Starting profile run: %s", profile)
    with log_path.open("w", encoding="utf-8") as log_file:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return {
        "profile": profile,
        "exit_code": completed.returncode,
        "results_dir": results_dir,
        "log_path": log_path,
    }


def _generate_profile_report(args: argparse.Namespace, profile: str, results_dir: Path, report_dir: Path) -> Path:
    result = finalize_mobile_report(
        project_root=PROJECT_ROOT,
        results_dir=results_dir,
        output_dir=report_dir,
        report_kind=args.report_kind,
        open_report=False,
        env_name=args.env,
        profile_name=profile,
        capabilities=_report_capabilities(profile, args),
        settings=ConfigReader(PROJECT_ROOT).read_settings(),
        history_dir=PROJECT_ROOT / "reports" / "history" / "device-matrix" / profile,
        logger=LOGGER,
    )
    for line in reporting_result_lines(result):
        if line.startswith(("Warning:", "Error:")):
            LOGGER.warning("%s: %s", profile, line)
        else:
            LOGGER.info("%s: %s", profile, line)
    report_path = preferred_report_path(result)
    if report_path:
        return report_path
    LOGGER.warning("No profile report was generated for %s.", profile)
    return report_dir / "index.html"


def _report_capabilities(profile: str, args: argparse.Namespace) -> dict:
    capabilities_config = ConfigReader(PROJECT_ROOT).read_capabilities()
    try:
        return resolve_capabilities(
            PROJECT_ROOT,
            capabilities_config,
            profile,
            overrides={
                "app": args.app,
                "device_name": args.device_name,
                "platform_version": args.platform_version,
                "udid": args.udid,
                "no_reset": args.no_reset,
                "full_reset": args.full_reset,
            },
        )
    except Exception as error:
        LOGGER.warning("Could not resolve mobile report metadata for profile %s: %s", profile, error)
        return capabilities_config.get("profiles", {}).get(profile, {})


def _append_optional(command: list[str], option: str, value: str | None) -> None:
    if value:
        command.extend([option, value])


def _retry_setting(name: str, default: int | float) -> int | float:
    return ConfigReader(PROJECT_ROOT).read_settings().get("retries", {}).get(name, default)


def _normalize_passthrough_args(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


if __name__ == "__main__":
    raise SystemExit(main())
