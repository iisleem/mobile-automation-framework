from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

from utils.allure_cli import get_allure_cli
from utils.capabilities import available_profiles
from utils.config_reader import ConfigReader
from utils.logger import get_logger
from utils.report_opener import open_report
from utils.reporting import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPORT_KIND,
    DEFAULT_RESULTS_DIR,
    REPORT_KIND_CHOICES,
    finalize_mobile_report,
    preferred_report_path,
    reporting_result_lines,
)


PROJECT_ROOT = Path(__file__).resolve().parent
LOGGER = get_logger("mobile-framework-cli")


class Doctor:
    def __init__(self) -> None:
        self.failed = 0
        self.warnings = 0

    def pass_(self, message: str) -> None:
        print(f"[PASS] {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"[WARN] {message}")

    def fail(self, message: str) -> None:
        self.failed += 1
        print(f"[FAIL] {message}")

    def exit_code(self, strict: bool = False) -> int:
        return 1 if self.failed or (strict and self.warnings) else 0


def main() -> int:
    parser = _build_parser()
    args, unknown_args = parser.parse_known_args()

    if args.command == "run":
        return _run_tests(args, unknown_args)
    if unknown_args:
        parser.error(f"Unknown arguments for '{args.command}': {' '.join(unknown_args)}")
    if args.command == "doctor":
        return _run_doctor(args)
    if args.command == "report":
        return _handle_report_command(args)
    if args.command == "helpers":
        return _open_helpers_catalog(args)

    parser.print_help()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="framework.py",
        description="Unified CLI for the mobile automation framework.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run tests locally or as a device/profile matrix.")
    run_parser.add_argument("--env", default="qa", help="Environment from config/environments.yaml.")
    run_parser.add_argument("--profile", help="Single capability profile.")
    run_parser.add_argument("--profiles", nargs="+", help="Run a profile matrix.")
    run_parser.add_argument("--profile-workers", type=int, help="Parallel profile suites for matrix execution.")
    run_parser.add_argument("--matrix", action="store_true", help="Run profiles from config/settings.yaml.")
    run_parser.add_argument("--appium-server", help="Override Appium server URL.")
    run_parser.add_argument("--device-name", help="Override appium:deviceName.")
    run_parser.add_argument("--platform-version", help="Override appium:platformVersion.")
    run_parser.add_argument("--udid", help="Override appium:udid.")
    run_parser.add_argument("--app", help="Override appium:app.")
    run_parser.add_argument("--no-reset", action="store_true", default=None, help="Set appium:noReset=true.")
    run_parser.add_argument("--full-reset", action="store_true", help="Set appium:fullReset=true.")
    run_parser.add_argument("-n", "--parallel", help="pytest-xdist worker count for test-case parallelism.")
    run_parser.add_argument("-m", "--markers", help="Raw pytest marker expression.")
    run_parser.add_argument("--smoke", action="store_true", help="Run smoke tests.")
    run_parser.add_argument("--regression", action="store_true", help="Run regression tests.")
    run_parser.add_argument("--e2e", action="store_true", help="Run e2e tests.")
    run_parser.add_argument("--android", action="store_true", help="Run Android-marked tests.")
    run_parser.add_argument("--ios", action="store_true", help="Run iOS-marked tests.")
    run_parser.add_argument("--native", action="store_true", help="Run native app tests.")
    run_parser.add_argument("--hybrid", action="store_true", help="Run hybrid app tests.")
    run_parser.add_argument("--mobile-web", action="store_true", help="Run mobile web tests through Appium.")
    run_parser.add_argument("--helpers", action="store_true", help="Run helper unit tests.")
    run_parser.add_argument("--android-example", action="store_true", help="Run the Android native example.")
    run_parser.add_argument("--ios-example", action="store_true", help="Run the iOS native example.")
    run_parser.add_argument("--hybrid-example", action="store_true", help="Run the hybrid demo app example.")
    run_parser.add_argument("--reruns", help="Retry failed tests.")
    run_parser.add_argument("--reruns-delay", help="Delay between retries.")
    run_parser.add_argument(
        "--report-kind",
        choices=REPORT_KIND_CHOICES,
        default=DEFAULT_REPORT_KIND,
        help="Post-run report kind: core, allure, both, or summary. Defaults to core.",
    )
    run_parser.add_argument("--no-open-report", action="store_true", help="Do not open generated reports.")
    run_parser.add_argument("--no-generate-report", action="store_true", help="Do not generate a post-run report.")

    report_parser = subparsers.add_parser("report", help="Generate or open reports.")
    report_subparsers = report_parser.add_subparsers(dest="report_command", required=True)
    report_open = report_subparsers.add_parser("open", help="Open the latest generated report.")
    report_open.add_argument("--type", choices=("auto", "core", "matrix", "summary", "allure"), default="auto")
    report_generate = report_subparsers.add_parser("generate", help="Generate a report from Allure results.")
    report_generate.add_argument("--results", default=str(DEFAULT_RESULTS_DIR))
    report_generate.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR))
    report_generate.add_argument(
        "--report-kind",
        choices=REPORT_KIND_CHOICES,
        default=DEFAULT_REPORT_KIND,
        help="Report kind: core, allure, both, or summary. Defaults to core.",
    )
    report_generate.add_argument("--env", default="qa", help="Environment metadata for the generated report.")
    report_generate.add_argument("--profile", help="Capability profile metadata for the generated report.")
    report_generate.add_argument("--no-open", action="store_true")

    helpers_parser = subparsers.add_parser("helpers", help="Open helper documentation.")
    helpers_parser.add_argument("--guide", action="store_true", help="Print the Markdown helper guide path.")

    doctor_parser = subparsers.add_parser("doctor", help="Check local machine and project readiness.")
    doctor_parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")

    return parser


def _run_tests(args: argparse.Namespace, extra_pytest_args: list[str]) -> int:
    marker_expression = _resolve_marker_expression(args)
    selected_profiles = _resolve_profiles(args)
    use_matrix = args.matrix or bool(args.profiles) or len(selected_profiles) > 1

    if use_matrix:
        command = [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_device_matrix.py"),
            "--env",
            args.env,
            "--profiles",
            *selected_profiles,
        ]
        if args.profile_workers is not None:
            command.extend(["--profile-workers", str(args.profile_workers)])
        _append_common_pytest_options(command, args, marker_expression, extra_pytest_args, include_profile=False)
        return _run_command(command)

    command = [sys.executable, "-m", "pytest", "--env", args.env]
    if selected_profiles:
        command.extend(["--profile", selected_profiles[0]])
    _append_common_pytest_options(command, args, marker_expression, extra_pytest_args, include_profile=False)

    if args.android_example:
        command.append("tests/examples/android")
    if args.ios_example:
        command.append("tests/examples/ios")
    if args.hybrid_example:
        command.append("tests/examples/hybrid")
    if args.helpers:
        command.append("tests/helpers")

    return _run_command(command)


def _append_common_pytest_options(
    command: list[str],
    args: argparse.Namespace,
    marker_expression: str | None,
    extra_pytest_args: list[str],
    include_profile: bool = True,
) -> None:
    if include_profile and args.profile:
        command.extend(["--profile", args.profile])
    if args.appium_server:
        command.extend(["--appium-server", args.appium_server])
    if args.device_name:
        command.extend(["--device-name", args.device_name])
    if args.platform_version:
        command.extend(["--platform-version", args.platform_version])
    if args.udid:
        command.extend(["--udid", args.udid])
    if args.app:
        command.extend(["--app", args.app])
    if args.no_reset:
        command.append("--no-reset")
    if args.full_reset:
        command.append("--full-reset")
    if marker_expression:
        command.extend(["-m", marker_expression])
    if args.parallel:
        command.extend(["-n", str(args.parallel)])
    reruns = args.reruns if args.reruns is not None else _retry_setting("default", 0)
    reruns_delay = args.reruns_delay if args.reruns_delay is not None else _retry_setting("delay_seconds", 0)
    if int(reruns):
        command.extend(["--reruns", str(reruns)])
    if float(reruns_delay):
        command.extend(["--reruns-delay", str(reruns_delay)])
    if args.report_kind != DEFAULT_REPORT_KIND:
        command.extend(["--report-kind", args.report_kind])
    if args.no_open_report:
        command.append("--no-open-report")
    if args.no_generate_report:
        command.append("--no-generate-report")
    command.extend(_normalize_passthrough_args(extra_pytest_args))


def _resolve_marker_expression(args: argparse.Namespace) -> str | None:
    selected = [
        marker
        for marker, enabled in {
            "smoke": args.smoke,
            "regression": args.regression,
            "e2e": args.e2e,
            "android": args.android or args.android_example,
            "ios": args.ios or args.ios_example,
            "native": args.native or args.android_example,
            "hybrid": args.hybrid or args.hybrid_example,
            "mobile_web": args.mobile_web,
            "helpers": args.helpers,
        }.items()
        if enabled
    ]
    expressions = selected[:]
    if args.markers:
        expressions.append(f"({args.markers})" if " " in args.markers else args.markers)
    return " and ".join(expressions) if expressions else None


def _resolve_profiles(args: argparse.Namespace) -> list[str]:
    settings = ConfigReader(PROJECT_ROOT).read_settings()
    if args.profile and args.profiles:
        raise SystemExit("Use either --profile or --profiles, not both.")
    if args.profiles:
        return args.profiles
    if args.profile:
        return [args.profile]
    if args.matrix:
        return settings.get("execution", {}).get("profiles", [])
    if getattr(args, "hybrid_example", False):
        return ["android_hybrid_demo"]
    return [settings["execution"]["default_profile"]]


def _normalize_passthrough_args(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def _retry_setting(name: str, default: int | float) -> int | float:
    return ConfigReader(PROJECT_ROOT).read_settings().get("retries", {}).get(name, default)


def _handle_report_command(args: argparse.Namespace) -> int:
    if args.report_command == "open":
        report_path = _find_report(args.type)
        if not report_path:
            print("No report found. Run tests first or generate a report.")
            return 1
        return 0 if open_report(report_path, LOGGER) else 1

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
        print(f"Primary report: {report_path}")
    return 0 if result.ok else 1


def _find_report(report_type: str) -> Path | None:
    candidates: list[Path] = []
    if report_type in {"auto", "core", "summary"}:
        candidates.append(PROJECT_ROOT / DEFAULT_OUTPUT_DIR / "index.html")
    if report_type in {"auto", "matrix"}:
        candidates.append(PROJECT_ROOT / "reports" / "device-matrix" / "index.html")
    if report_type == "allure":
        candidates.extend(
            [
                PROJECT_ROOT / DEFAULT_OUTPUT_DIR / "allure" / "index.html",
                PROJECT_ROOT / "reports" / "allure-report" / "index.html",
            ]
        )
    existing = [path for path in candidates if path.exists()]
    return max(existing, key=lambda path: path.stat().st_mtime) if existing else None


def _report_capabilities(profile_name: str) -> dict:
    from utils.capabilities import resolve_capabilities

    capabilities_config = ConfigReader(PROJECT_ROOT).read_capabilities()
    try:
        return resolve_capabilities(PROJECT_ROOT, capabilities_config, profile_name)
    except Exception as error:
        LOGGER.warning("Could not resolve mobile report metadata for profile %s: %s", profile_name, error)
        return capabilities_config.get("profiles", {}).get(profile_name, {})


def _open_helpers_catalog(args: argparse.Namespace) -> int:
    path = PROJECT_ROOT / "docs" / ("FRAMEWORK_HELPERS.md" if args.guide else "helpers_catalog.html")
    if args.guide:
        print(path)
        return 0 if path.exists() else 1
    return 0 if open_report(path, LOGGER) else 1


def _run_doctor(args: argparse.Namespace) -> int:
    doctor = Doctor()
    print("Mobile Framework Doctor\n=======================")
    _check_python(doctor)
    _check_project_files(doctor)
    _check_yaml_config(doctor)
    _check_python_dependencies(doctor)
    _check_cli_tools(doctor)
    _check_appium_server(doctor)
    _check_sample_apps(doctor)
    _check_allure(doctor)

    print("\nSummary")
    print(f"Failures: {doctor.failed}")
    print(f"Warnings: {doctor.warnings}")
    if doctor.exit_code(args.strict):
        print("Status: NOT READY")
    elif doctor.warnings:
        print("Status: READY WITH WARNINGS")
    else:
        print("Status: READY")
    return doctor.exit_code(args.strict)


def _check_python(doctor: Doctor) -> None:
    if sys.version_info >= (3, 11):
        doctor.pass_(f"Python {sys.version.split()[0]} is supported.")
    else:
        doctor.fail("Python 3.11+ is recommended.")


def _check_project_files(doctor: Doctor) -> None:
    required = [
        "config/settings.yaml",
        "config/capabilities.yaml",
        "conftest.py",
        "framework.py",
        "pytest.ini",
        "requirements.txt",
        "docs/FRAMEWORK_HELPERS.md",
    ]
    for relative in required:
        path = PROJECT_ROOT / relative
        if path.exists():
            doctor.pass_(f"Found {relative}")
        else:
            doctor.fail(f"Missing {relative}")


def _check_yaml_config(doctor: Doctor) -> None:
    try:
        reader = ConfigReader(PROJECT_ROOT)
        settings = reader.read_settings()
        profiles = available_profiles(reader.read_capabilities())
        if settings.get("execution", {}).get("default_profile") in profiles:
            doctor.pass_("YAML config loaded and default profile exists.")
        else:
            doctor.fail("Default profile does not exist in config/capabilities.yaml.")
    except Exception as error:
        doctor.fail(f"YAML config error: {error}")


def _check_python_dependencies(doctor: Doctor) -> None:
    for module in ("pytest", "yaml", "requests", "selenium", "appium", "automation_core"):
        if importlib.util.find_spec(module):
            doctor.pass_(f"Python dependency importable: {module}")
        else:
            doctor.fail(f"Python dependency missing: {module}")


def _check_cli_tools(doctor: Doctor) -> None:
    for command in ("node", "npm", "appium"):
        if shutil.which(command):
            doctor.pass_(f"CLI available: {command}")
        else:
            doctor.warn(f"CLI not found: {command}")
    if shutil.which("adb"):
        doctor.pass_("Android adb available.")
    else:
        doctor.warn("Android adb not found. Android runs need platform-tools in PATH.")
    if sys.platform == "darwin":
        if not shutil.which("xcrun"):
            doctor.warn("xcrun not found. iOS simulator runs need Xcode command line tools.")
        else:
            simctl = subprocess.run(["xcrun", "--find", "simctl"], capture_output=True, text=True)
            if simctl.returncode == 0:
                doctor.pass_(f"iOS simulator tool available: {simctl.stdout.strip()}")
            else:
                selected_dir = _selected_developer_dir()
                developer_dir = os.getenv("DEVELOPER_DIR")
                context = (
                    f" DEVELOPER_DIR={developer_dir}." if developer_dir else f" Selected developer dir: {selected_dir}."
                )
                doctor.warn(
                    "iOS simulator tool `simctl` not found."
                    f"{context} Use DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer for iOS commands "
                    "or select a full Xcode install with xcode-select when needed."
                )


def _check_appium_server(doctor: Doctor) -> None:
    from utils.mobile_driver import is_appium_server_ready

    server_url = ConfigReader(PROJECT_ROOT).read_settings()["appium"]["server_url"]
    if is_appium_server_ready(server_url):
        doctor.pass_(f"Appium server reachable: {server_url}")
    else:
        doctor.warn(f"Appium server not reachable at {server_url}. Start it before device tests.")


def _selected_developer_dir() -> str:
    selected = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True)
    return selected.stdout.strip() if selected.returncode == 0 else "unknown"


def _check_sample_apps(doctor: Doctor) -> None:
    android_app = PROJECT_ROOT / "apps" / "TheApp.apk"
    ios_app = PROJECT_ROOT / "apps" / "TheApp.app.zip"
    if android_app.exists():
        doctor.pass_("Android sample app is present.")
    else:
        doctor.warn("Android sample app missing. Run: python scripts/download_sample_apps.py --android")
    if ios_app.exists():
        doctor.pass_("iOS sample app is present.")
    else:
        doctor.warn("iOS sample app missing. Run: python scripts/download_sample_apps.py --ios")


def _check_allure(doctor: Doctor) -> None:
    if get_allure_cli(PROJECT_ROOT, LOGGER):
        doctor.pass_("Allure CLI available.")
    else:
        doctor.warn("Allure CLI not found. Core product reports are available by default; official Allure is optional.")


def _run_command(command: list[str]) -> int:
    print("+ " + " ".join(command))
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
