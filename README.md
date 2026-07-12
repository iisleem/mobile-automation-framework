# Mobile Automation Framework User Guide

[![Mobile Framework Validation](https://github.com/iisleem/mobile-automation-framework/actions/workflows/mobile-framework.yml/badge.svg)](https://github.com/iisleem/mobile-automation-framework/actions/workflows/mobile-framework.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Appium](https://img.shields.io/badge/mobile-Appium-662D91.svg)](https://appium.io/)
[![Pytest](https://img.shields.io/badge/tested%20with-pytest-0A9EDC.svg)](https://pytest.org/)
[![Allure](https://img.shields.io/badge/reports-Allure-orange.svg)](https://allurereport.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Standalone Python mobile automation framework for Android and iOS native, hybrid, and mobile
web experiences. It uses Appium 2, Pytest, Screen Object Model, reusable flows, capability
profiles, failure artifacts, Allure-compatible reporting, and a helper library focused on real
mobile automation work.

This repo is intentionally independent from any web automation framework. Shared utilities such
as API setup, polling, files, and test data are included only because they are useful in mobile
test setup, cleanup, and assertions.

## What This Framework Gives You

- Android and iOS automation through Appium capability profiles
- Native app, hybrid app, and mobile web support through Appium sessions
- Clean Screen Object Model with locators kept out of test files
- Reusable flows for business journeys and sample app scenarios
- Unified CLI for doctor checks, test runs, reports, helper docs, and profile matrix runs
- YAML settings, environments, and capabilities
- CLI overrides for profile, Appium server, app path, device name, platform version, UDID, reset behavior, markers, retries, and parallel execution
- Device/profile matrix execution with an HTML dashboard
- Screenshots, page source dumps, Appium logs, and optional screen recordings on failed tests
- Allure report generation when the Allure CLI exists, with a built-in HTML fallback
- Self-healing locator fallback support in `BaseScreen`
- Action-level retries with post-action verification for mobile-sensitive actions
- iOS keyboard typing helper for secure fields and simulator keyboard-sensitive inputs
- Mobile helpers for gestures, contexts, app lifecycle, permissions, deep links, clipboard, device state, accessibility, visual checks, polling, API setup, files, text extraction, test data, and soft assertions
- Runnable Android native example using TheApp
- Runnable iOS native example using TheApp
- Runnable mobile web smoke example for Android Chrome or iOS Safari Appium profiles
- Helper unit tests that run without a connected device
- Feature parity notes that explain supported mobile features and intentionally excluded web-only utilities
- GitHub Actions validation for helper tests, static checks, and report artifacts

## Project Structure

```text
mobile-automation-framework/
├── apps/                         # Local .apk, .app, .app.zip, or .ipa app fixtures
├── config/
│   ├── settings.yaml             # Timeouts, Appium server, artifacts, matrix defaults
│   ├── environments.yaml         # API endpoints and environment-level values
│   └── capabilities.yaml         # Android/iOS capability profiles
├── screens/
│   ├── base_screen.py            # Shared mobile screen actions and self-healing locators
│   ├── mobile_web/               # Appium mobile browser screen object
│   └── the_app/                  # Cross-platform sample app screen objects
├── flows/
│   └── the_app/                  # Cross-platform sample app flows
├── tests/
│   ├── examples/android/         # Runnable Android native example
│   ├── examples/ios/             # Runnable iOS native example
│   ├── examples/mobile_web/      # Runnable Appium mobile web smoke example
│   └── helpers/                  # Fast helper/unit tests
├── utils/
│   ├── helpers/                  # Reusable mobile automation helper library
│   ├── capabilities.py           # Capability profile resolver
│   ├── mobile_driver.py          # Appium driver factory
│   ├── report_generator.py       # Built-in HTML reports and matrix dashboard
│   └── artifact_helper.py        # Failure screenshots, logs, source dumps, recordings
├── scripts/
│   ├── download_sample_apps.py   # Downloads TheApp Android/iOS fixtures
│   ├── run_device_matrix.py      # Runs one pytest suite per profile
│   └── generate_allure_report.py # Manual report generation helper
├── docs/
│   ├── FRAMEWORK_HELPERS.md
│   ├── FEATURE_PARITY.md
│   ├── TROUBLESHOOTING.md
│   └── helpers_catalog.html
├── conftest.py                   # Pytest hooks and fixtures
├── framework.py                  # Unified framework CLI
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

## Requirements

- Python 3.11+
- Node.js and npm for Appium
- Appium 2 with `uiautomator2` and `xcuitest` drivers for device runs
- Android SDK platform tools for Android runs
- Full Xcode for iOS simulator runs on macOS

## Quick Start

```bash
cd mobile-automation-framework
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python framework.py doctor
python framework.py run --helpers --no-open-report
```

Install Appium 2 and mobile drivers:

```bash
npm install -g appium
appium driver install uiautomator2
appium driver install xcuitest
appium --base-path /
```

The runnable native examples auto-download their TheApp sample build the first time they run.
You can also download both fixtures manually:

```bash
python scripts/download_sample_apps.py --all
```

## Local Validation

Use these commands before opening a PR:

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m compileall -q framework.py conftest.py screens flows utils scripts tests
ruff check .
python framework.py run --helpers --no-open-report --no-generate-report
```

Device examples require Appium and a prepared emulator, simulator, or real device. The helper suite
is intentionally device-free so CI can validate framework behavior quickly.

## Run The Android Example

Prepare an Android emulator or device, start Appium, then run:

```bash
python framework.py run --android-example --profile android_the_app
```

The Android example opens TheApp, navigates to the native login screen, logs in with sample
credentials, and demonstrates screen objects, flows, device helpers, accessibility checks,
and failure artifacts.

## Run The iOS Example

Start an iOS simulator and Appium with the XCUITest driver:

```bash
python framework.py run --ios-example --profile ios_the_app --device-name "iPhone 15"
```

The iOS example opens the native TheApp simulator build and runs the same login journey through
iOS/Appium capabilities.

If your machine has full Xcode installed but `xcode-select -p` still points to Command Line Tools,
prefix iOS commands with:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer python framework.py run --ios-example --profile ios_the_app
```

## Run Mobile Web

Mobile web is supported through Appium browser sessions, not through Playwright or the separate
web framework. The bundled example is self-contained: Android uses a `data:` URL for emulators
without a network route, and iOS serves the same tiny HTML page locally for Safari.

```bash
python framework.py run --mobile-web --profile android_mobile_web
python framework.py run --mobile-web --profile ios_mobile_web --device-name "iPhone 15"
```

For real site tests, the configured URL fixture lives in `config/environments.yaml` as
`mobile_web_url`.

## Unified CLI

Run helper tests:

```bash
python framework.py run --helpers
```

Run a specific profile:

```bash
python framework.py run --profile android_the_app -m smoke
python framework.py run --profile android_mobile_web --mobile-web
```

Override device details:

```bash
python framework.py run --profile ios_the_app --device-name "iPhone 15 Pro" --platform-version "18.0"
```

Run on a real device or simulator UDID:

```bash
python framework.py run --profile android_the_app --udid emulator-5554
python framework.py run --profile ios_the_app --udid YOUR-IOS-UDID
```

Run a profile matrix:

```bash
python framework.py run --matrix
python framework.py run --profiles android_the_app ios_the_app android_mobile_web ios_mobile_web --profile-workers 2
```

Retry behavior is split into two layers:

```yaml
retries:
  default: 1              # pytest test-case reruns
  delay_seconds: 1
  action_default: 3       # BaseScreen action retries
  action_delay_seconds: 0.3
```

`default` is passed to `pytest-rerunfailures`. `action_default` is used inside screen actions such
as `tap`, `type_text`, and `type_text_with_keyboard`; if an action command succeeds but the expected
UI state does not change, the action is retried and then fails at the action step.

Open reports and docs:

```bash
python framework.py report open
python framework.py report generate
python framework.py helpers
python framework.py helpers --guide
```

For the web-to-mobile concept comparison, see `docs/FEATURE_PARITY.md`.
For setup and device issues, see `docs/TROUBLESHOOTING.md`.

## Capability Profiles

Profiles live in `config/capabilities.yaml`.

```yaml
profiles:
  android_the_app:
    platformName: Android
    appium:automationName: UiAutomator2
    appium:deviceName: "Android Emulator"
    appium:app: "apps/TheApp.apk"

  ios_the_app:
    platformName: iOS
    appium:automationName: XCUITest
    appium:deviceName: "iPhone 15"
    appium:app: "apps/TheApp.app.zip"

  android_mobile_web:
    platformName: Android
    browserName: Chrome
    appium:automationName: UiAutomator2
    appium:deviceName: "Android Emulator"

  ios_mobile_web:
    platformName: iOS
    browserName: Safari
    appium:automationName: XCUITest
    appium:deviceName: "iPhone 15"
```

Use environment interpolation for local-only values:

```yaml
appium:platformVersion: "${IOS_PLATFORM_VERSION:-}"
appium:app: "${IOS_APP:-apps/YourApp.app.zip}"
```

## Writing Tests

Keep tests readable and push UI details into screens and flows:

```python
import pytest

from flows.the_app import TheAppLoginFlow


pytestmark = [pytest.mark.android, pytest.mark.native, pytest.mark.smoke]


def test_android_the_app_login_flow(mobile_driver):
    TheAppLoginFlow(mobile_driver).login_successfully()
```

Hybrid apps can switch from native to webview context with `ContextHelper`:

```python
from utils.helpers.contexts import ContextHelper


def test_hybrid_checkout(mobile_driver):
    contexts = ContextHelper(mobile_driver)
    contexts.switch_to_webview()
    assert "WEBVIEW" in contexts.current_context()
    contexts.switch_to_native()
```

Mobile web tests use Appium browser profiles:

```python
import pytest

from screens.mobile_web import MobileBrowserScreen


pytestmark = [pytest.mark.mobile_web, pytest.mark.smoke]


def test_mobile_browser(mobile_driver, mobile_web_example_url):
    browser = MobileBrowserScreen(mobile_driver)
    browser.open_url(mobile_web_example_url)
    browser.assert_title_contains("Appium Mobile Web Example")
```

Create locators in screen objects:

```python
from appium.webdriver.common.appiumby import AppiumBy
from screens.base_screen import BaseScreen


class LoginScreen(BaseScreen):
    @property
    def username(self):
        return self.locator_with_fallbacks(
            "Username field",
            (AppiumBy.ACCESSIBILITY_ID, "username"),
            (AppiumBy.ID, "com.example:id/username"),
        )
```

For iOS secure fields that do not accept normal `send_keys`, use the keyboard-backed action:

```python
self.type_text_with_keyboard(self.password_field, "mypassword", clear_first=False)
```

## Self-Healing Locators

The framework supports conservative self-healing locators in `BaseScreen`. A screen can define a
primary locator and fallback locators; if the primary locator is not found, the framework tries the
fallbacks in order and logs when a fallback is used.

```python
self.locator_with_fallbacks(
    "Login button",
    (AppiumBy.ACCESSIBILITY_ID, "loginBtn"),
    (AppiumBy.XPATH, "//*[@name='loginBtn' or @resource-id='loginBtn']"),
)
```

This matches the web framework concept: it is engineer-defined fallback healing, not AI-based
auto-healing that invents selectors at runtime.

## CI And Reports

The GitHub Actions workflow runs on pushes, pull requests, and manual dispatch. It installs Python
dependencies, runs compile checks, runs `ruff check .`, executes helper tests, and uploads generated
reports/artifacts.

Real Android and iOS device tests are kept out of the default hosted CI because they need Appium,
emulator/simulator setup, Xcode for iOS, and device-specific timing. Run them locally or move them to
a self-hosted runner when the device lab is ready.

## Known Limits

- The bundled examples cover native and mobile web. Hybrid support is implemented through
  `ContextHelper`, but this repo does not bundle a separate hybrid sample app.
- Self-healing means engineer-defined fallback locators. AI-based auto-healing is intentionally out
  of scope for this release.
- Sample app binaries and generated reports are gitignored. Download sample apps locally with
  `python scripts/download_sample_apps.py --all`.

## References

- [Appium documentation](https://appium.io/docs/en/latest/)
- [Appium Python Client](https://github.com/appium/python-client)
- [UiAutomator2 driver](https://github.com/appium/appium-uiautomator2-driver)
- [TheApp sample application](https://github.com/appium-pro/TheApp)
