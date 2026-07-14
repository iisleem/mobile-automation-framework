# Mobile Feature Parity Notes

This framework follows the same product idea as the web framework: a runnable automation starter
with a clear CLI, page/screen objects, helper docs, reports, retries, and practical examples. It is
not a web framework copy. Web-only code is intentionally excluded unless it also solves a real
mobile automation problem.

## Supported Core Capabilities

| Capability | Mobile status | Notes |
| --- | --- | --- |
| Unified CLI | Supported | `framework.py` handles doctor checks, runs, reports, helper docs, examples, and profile matrix runs. |
| Pytest execution | Supported | Markers, xdist workers, pytest reruns, and passthrough pytest args are supported. |
| Test-case retry | Supported | `retries.default` and `retries.delay_seconds` are applied by the main CLI and device matrix runner. |
| Action-level retry | Supported | `BaseScreen.tap`, `type_text`, and `type_text_with_keyboard` retry mobile actions before the next step runs. |
| Post-action verification | Supported | Taps can verify a locator or callback, and text entry verifies that the field value changed. |
| Reports | Supported | Core product report is the default at `reports/automation-report/index.html`; official Allure is optional via `--report-kind allure` or `--report-kind both`. |
| Failure artifacts | Supported | Screenshots, page source dumps, logs, and optional recordings on failed tests. |
| Screen Object Model | Supported | Mobile tests use `screens/` and `flows/` instead of web pages. |
| Self-healing locators | Supported | Engineer-defined fallback locators through `locator_with_fallbacks`; no runtime selector invention. |
| Android native | Supported | `android_the_app` profile and runnable TheApp example. |
| iOS native | Supported | `ios_the_app` profile and runnable TheApp example. |
| Hybrid apps | Supported | `ContextHelper` switches between `NATIVE_APP` and webview contexts; Android WebView and iOS WKWebView samples are included from source. |
| Mobile web | Supported | Appium Chrome/Safari profiles and a runnable mobile web smoke example. |
| Profile matrix | Supported | `scripts/run_device_matrix.py` runs one pytest suite per capability profile and builds a dashboard. |
| Helper catalog | Supported | `docs/FRAMEWORK_HELPERS.md` and `docs/helpers_catalog.html` document reusable helpers. |

## Reporting Modes

The post-run report flow reads `reports/allure-results` and generates the shared core product
report by default. Use `--report-kind core|allure|both|summary` from `framework.py run`,
`framework.py report generate`, or `scripts/generate_allure_report.py` to choose another mode.

`both` keeps the core product report as the primary output and attempts official Allure HTML as an
optional extra. If the Allure CLI is missing or fails in `both` mode, the successful core report is
kept and the run is not failed because of official Allure generation.

## Mobile-Specific Helper Coverage

| Area | Mobile helper |
| --- | --- |
| Gestures | `GestureHelper` for scroll, swipe, long press, coordinate taps. |
| Contexts | `ContextHelper` for native, webview, and mobile browser contexts. |
| App lifecycle | `AppHelper` for install, remove, activate, terminate, and state checks. |
| Device state | `DeviceHelper` for orientation, backgrounding, lock/unlock, and battery info. |
| Permissions | `PermissionHelper` for Android runtime permissions and alert handling. |
| Deep links | `DeepLinkHelper` for Android deep links and universal links. |
| Clipboard | `ClipboardHelper` for mobile clipboard reads/writes. |
| iOS typing | `BaseScreen.type_text_with_keyboard` for secure fields and keyboard-sensitive inputs. |

## Shared Concepts Kept Because They Help Mobile

| Area | Why it stays |
| --- | --- |
| API helpers | Mobile tests often need backend setup, cleanup, and assertions. |
| Polling helpers | Useful for async jobs, push/SMS/email backends, file creation, and API state. |
| Text helpers | Useful for OTP extraction, SMS text, push text, and normalized assertions. |
| Data generators | Useful for unique accounts, usernames, emails, and phone values. |
| File helpers | Useful for artifacts, generated files, and upload/download-adjacent flows. |
| Visual helpers | Useful for screenshot capture and baseline checks. |
| Accessibility helpers | Useful for detecting unlabeled mobile controls from page source. |
| Soft assertions | Useful when collecting multiple mobile state checks before failing. |

## Web-Only Features Not Copied

| Web feature area | Mobile decision |
| --- | --- |
| Browser storage/session helpers | Excluded. Native mobile apps do not use browser local/session storage. |
| Cookie helpers | Excluded by default. Add only when a mobile web or webview suite needs cookie-level control. |
| Browser console/network helpers | Excluded by default. Appium mobile sessions expose different diagnostics than Playwright browser contexts. |
| Browser form/table helpers | Excluded. Mobile UI flows use screen objects and app-specific locators instead. |
| Download/upload browser helpers | Excluded. Native mobile file flows should be implemented with app/device-specific helpers. |
| Database helper | Excluded by default. Projects can add it when the product test strategy requires direct DB setup. |
| Browser PDF/security/performance helpers | Excluded by default because they are browser-centric. Add targeted mobile equivalents only when needed. |

## Self-Healing And Auto-Healing

The web and mobile frameworks both support conservative self-healing: engineers define a primary
locator and ordered fallbacks. If the primary locator fails, the framework tries the fallback
locators and logs which fallback was used.

Neither framework currently performs AI auto-healing that invents new locators at runtime. That is a
different feature with different risk: it can hide product changes if it is not heavily audited.

## Retry Model

Mobile has two retry layers:

| Retry layer | Scope | Default source |
| --- | --- | --- |
| Test-case retry | Re-runs a failed pytest test case. | `retries.default` and `retries.delay_seconds`. |
| Action retry | Re-runs one mobile action before moving to the next action. | `retries.action_default` and `retries.action_delay_seconds`. |

Action retry is especially important for mobile because Appium commands can return successfully
while the UI did not actually change. The framework verifies text entry and optional post-tap state
so the failure points to the real action that broke.
