from __future__ import annotations

from pathlib import Path
from typing import Generator
from urllib.request import urlretrieve

import pytest

from utils.artifact_helper import (
    capture_failure_artifacts,
    safe_artifact_name,
    save_screen_recording,
)
from utils.capabilities import resolve_capabilities
from utils.config_reader import ConfigReader
from utils.helpers.api import ApiClient
from utils.helpers.device import dismiss_android_system_dialogs
from utils.logger import get_logger
from utils.mobile_driver import create_mobile_driver, describe_capabilities, is_appium_server_ready
from utils.reporting import (
    DEFAULT_REPORT_KIND,
    DEFAULT_RESULTS_DIR,
    REPORT_KIND_CHOICES,
    finalize_mobile_report,
    preferred_report_path,
    reporting_result_lines,
)


PROJECT_ROOT = Path(__file__).resolve().parent
LOGGER = get_logger("mobile-framework")
ARTIFACT_DIRECTORIES = ("reports/allure-results", "screenshots", "source_dumps", "recordings", "logs")


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("mobile-automation-framework")
    group.addoption("--env", default="qa", help="Environment from config/environments.yaml.")
    group.addoption("--profile", help="Capability profile from config/capabilities.yaml.")
    group.addoption("--appium-server", help="Appium server URL. Defaults to config/settings.yaml.")
    group.addoption("--device-name", help="Override appium:deviceName.")
    group.addoption("--platform-version", help="Override appium:platformVersion.")
    group.addoption("--udid", help="Override appium:udid for a real device or simulator.")
    group.addoption("--app", help="Override appium:app.")
    group.addoption("--no-reset", action="store_true", default=None, help="Set appium:noReset=true.")
    group.addoption("--full-reset", action="store_true", default=False, help="Set appium:fullReset=true.")
    group.addoption(
        "--report-kind",
        choices=REPORT_KIND_CHOICES,
        default=DEFAULT_REPORT_KIND,
        help="Post-run report kind: core, allure, both, or summary. Defaults to core.",
    )
    group.addoption("--no-generate-report", action="store_true", default=False)
    group.addoption("--no-open-report", action="store_true", default=False)


def pytest_configure(config: pytest.Config) -> None:
    for directory in ARTIFACT_DIRECTORIES:
        (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    profile_name = _profile_name(config)
    profile = _profile_capabilities(profile_name)
    platform_name = str(profile.get("platformName", "")).lower()
    is_mobile_web_profile = bool(profile.get("browserName"))
    android_skip = pytest.mark.skip(reason=f"Selected profile '{profile_name}' is not Android.")
    ios_skip = pytest.mark.skip(reason=f"Selected profile '{profile_name}' is not iOS.")
    native_skip = pytest.mark.skip(reason=f"Selected profile '{profile_name}' is a mobile web profile.")
    mobile_web_skip = pytest.mark.skip(reason=f"Selected profile '{profile_name}' is a native app profile.")

    for item in items:
        if "android" in item.keywords and platform_name != "android":
            item.add_marker(android_skip)
        if "ios" in item.keywords and platform_name != "ios":
            item.add_marker(ios_skip)
        if "native" in item.keywords and is_mobile_web_profile:
            item.add_marker(native_skip)
        if "mobile_web" in item.keywords and not is_mobile_web_profile:
            item.add_marker(mobile_web_skip)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if hasattr(session.config, "workerinput"):
        return
    if session.config.getoption("--no-generate-report"):
        return

    _generate_report_after_session(
        session.config,
        open_report=not session.config.getoption("--no-open-report"),
    )


@pytest.fixture(scope="session")
def framework_config(pytestconfig: pytest.Config) -> dict:
    env_name = pytestconfig.getoption("--env")
    config = ConfigReader(PROJECT_ROOT).load(env_name)
    LOGGER.info("Loaded config for environment: %s", env_name)
    return config


@pytest.fixture(scope="session")
def api_client(framework_config: dict) -> ApiClient:
    return ApiClient(framework_config["environment_config"]["api_base_url"])


@pytest.fixture(scope="session")
def mobile_web_url(framework_config: dict) -> str:
    return framework_config["environment_config"]["mobile_web_url"]


@pytest.fixture(scope="session")
def capability_profile_name(pytestconfig: pytest.Config) -> str:
    return _profile_name(pytestconfig)


@pytest.fixture(scope="session")
def mobile_capabilities(pytestconfig: pytest.Config) -> dict:
    capabilities_config = ConfigReader(PROJECT_ROOT).read_capabilities()
    return resolve_capabilities(
        PROJECT_ROOT,
        capabilities_config,
        _profile_name(pytestconfig),
        overrides={
            "app": pytestconfig.getoption("--app"),
            "device_name": pytestconfig.getoption("--device-name"),
            "platform_version": pytestconfig.getoption("--platform-version"),
            "udid": pytestconfig.getoption("--udid"),
            "no_reset": pytestconfig.getoption("--no-reset"),
            "full_reset": pytestconfig.getoption("--full-reset"),
        },
    )


@pytest.fixture
def mobile_driver(
    pytestconfig: pytest.Config,
    framework_config: dict,
    mobile_capabilities: dict,
    request: pytest.FixtureRequest,
) -> Generator:
    server_url = pytestconfig.getoption("--appium-server") or framework_config["appium"]["server_url"]
    _assert_app_path_ready(mobile_capabilities, framework_config)
    _assert_appium_server_ready(server_url)

    LOGGER.info("Creating Appium session with capabilities:\n%s", describe_capabilities(mobile_capabilities))
    driver = create_mobile_driver(server_url, mobile_capabilities)
    driver.implicitly_wait(0)
    dismiss_android_system_dialogs(driver, LOGGER)

    recording_started = _start_recording_if_enabled(driver, framework_config)
    try:
        yield driver
    finally:
        failed = bool(getattr(request.node, "rep_call", None) and request.node.rep_call.failed)
        test_name = safe_artifact_name(request.node.nodeid)

        if failed:
            capture_failure_artifacts(driver, PROJECT_ROOT, framework_config, test_name)

        _stop_recording_if_needed(driver, framework_config, test_name, failed, recording_started)
        try:
            driver.quit()
        except Exception as error:
            LOGGER.warning("Could not quit Appium session cleanly: %s", error)


@pytest.fixture
def driver(mobile_driver):
    return mobile_driver


def _profile_name(config: pytest.Config) -> str:
    configured = ConfigReader(PROJECT_ROOT).read_settings()["execution"]["default_profile"]
    return config.getoption("--profile") or configured


def _profile_platform(profile_name: str) -> str:
    return str(_profile_capabilities(profile_name).get("platformName", ""))


def _profile_capabilities(profile_name: str) -> dict:
    capabilities = ConfigReader(PROJECT_ROOT).read_capabilities()
    return capabilities.get("profiles", {}).get(profile_name, {})


def _assert_appium_server_ready(server_url: str) -> None:
    if is_appium_server_ready(server_url):
        return
    pytest.fail(
        f"Appium server is not reachable at {server_url}. Start it with `appium --base-path /` or pass --appium-server."
    )


def _assert_app_path_ready(capabilities: dict, framework_config: dict) -> None:
    app_path = capabilities.get("appium:app")
    if not app_path or "://" in str(app_path):
        return
    path = Path(app_path)
    if path.exists():
        return
    if _download_known_sample_app(path, framework_config):
        return
    pytest.fail(f"App file does not exist: {app_path}. {_missing_app_hint(path)}")


def _download_known_sample_app(path: Path, framework_config: dict) -> bool:
    sample_apps = framework_config.get("sample_apps", {})
    urls_by_name = {
        "TheApp.apk": sample_apps.get("the_app_android_url"),
        "TheApp.app.zip": sample_apps.get("the_app_ios_url"),
    }
    url = urls_by_name.get(path.name)
    if not url:
        return False
    try:
        LOGGER.info("Sample app missing. Downloading %s to %s", url, path)
        path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(url, path)
        return path.exists()
    except Exception as error:
        LOGGER.warning("Could not download sample app %s: %s", url, error)
        return False


def _missing_app_hint(path: Path) -> str:
    if path.name.startswith("HybridDemo"):
        return "Run `python scripts/build_hybrid_sample_apps.py --all` or override with --app."
    return "Run `python scripts/download_sample_apps.py --all` or override with --app."


def _start_recording_if_enabled(driver, framework_config: dict) -> bool:
    if not framework_config.get("recording", {}).get("enabled", False):
        return False
    try:
        driver.start_recording_screen()
        return True
    except Exception as error:
        LOGGER.warning("Could not start screen recording: %s", error)
        return False


def _stop_recording_if_needed(
    driver,
    framework_config: dict,
    test_name: str,
    failed: bool,
    recording_started: bool,
) -> None:
    if not recording_started:
        return
    try:
        encoded = driver.stop_recording_screen()
    except Exception as error:
        LOGGER.warning("Could not stop screen recording: %s", error)
        return
    if failed:
        save_screen_recording(encoded, PROJECT_ROOT, framework_config, test_name)


def _generate_report_after_session(config: pytest.Config, *, open_report: bool) -> Path | None:
    profile_name = _profile_name(config)
    result = finalize_mobile_report(
        project_root=PROJECT_ROOT,
        results_dir=DEFAULT_RESULTS_DIR,
        report_kind=config.getoption("--report-kind"),
        open_report=open_report,
        env_name=config.getoption("--env"),
        profile_name=profile_name,
        capabilities=_report_capabilities(config, profile_name),
        settings=ConfigReader(PROJECT_ROOT).read_settings(),
        logger=LOGGER,
    )
    for line in reporting_result_lines(result):
        if line.startswith(("Warning:", "Error:")):
            LOGGER.warning(line)
        else:
            LOGGER.info(line)
    if not result.ok:
        LOGGER.warning("Post-run reporting did not produce the requested primary report.")
    return preferred_report_path(result)


def _report_capabilities(config: pytest.Config, profile_name: str) -> dict:
    capabilities_config = ConfigReader(PROJECT_ROOT).read_capabilities()
    try:
        return resolve_capabilities(
            PROJECT_ROOT,
            capabilities_config,
            profile_name,
            overrides={
                "app": config.getoption("--app"),
                "device_name": config.getoption("--device-name"),
                "platform_version": config.getoption("--platform-version"),
                "udid": config.getoption("--udid"),
                "no_reset": config.getoption("--no-reset"),
                "full_reset": config.getoption("--full-reset"),
            },
        )
    except Exception as error:
        LOGGER.warning("Could not resolve mobile report metadata for profile %s: %s", profile_name, error)
        return _profile_capabilities(profile_name)
