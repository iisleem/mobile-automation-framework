# Framework Helpers Catalog

Reusable helpers for common mobile automation tasks. Helpers are intentionally small and explicit
so tests stay readable without hiding product behavior.

Environment-neutral helpers such as polling, files, text extraction, test data, and soft assertions
keep their mobile import paths while delegating shared behavior to `automation-core`. Appium-specific
helpers for gestures, contexts, devices, permissions, apps, clipboard, and visual checks remain
mobile-owned.

## Helper Index

| Helper | Category | Tags | Description |
| --- | --- | --- | --- |
| `GestureHelper.scroll_down`, `scroll_up`, `swipe` | Gestures | swipe, scroll, touch | Cross-platform gesture wrappers with Appium fallbacks. |
| `GestureHelper.long_press`, `tap_coordinates` | Gestures | long press, coordinates | Performs coordinate and element-level gestures. |
| `ContextHelper.contexts` | Contexts | native, webview, hybrid, mobile web | Lists available native, in-app webview, and mobile browser contexts. |
| `ContextHelper.switch_to_native` | Contexts | native | Switches to `NATIVE_APP`. |
| `ContextHelper.switch_to_webview` | Contexts | hybrid, webview | Switches to a matching in-app webview context by name, title, URL, or bundle id. |
| `DeviceHelper.rotate_portrait`, `rotate_landscape` | Device | orientation | Changes device orientation. |
| `DeviceHelper.background_app`, `lock`, `unlock` | Device | lifecycle | Sends the app/device to background, locks, or unlocks. |
| `DeviceHelper.battery_info` | Device | battery | Reads mobile battery info through Appium extensions. |
| `AppHelper.install_app`, `remove_app` | Apps | install, cleanup | Installs or removes apps during setup/cleanup. |
| `AppHelper.activate`, `terminate`, `state` | Apps | lifecycle | Controls application state. |
| `PermissionHelper.grant_android_permission` | Permissions | android, shell | Grants Android runtime permissions through Appium mobile shell. |
| `PermissionHelper.revoke_android_permission` | Permissions | android, shell | Revokes Android runtime permissions. |
| `PermissionHelper.accept_alert_if_present` | Permissions | alerts | Handles iOS/Android permission alerts safely. |
| `DeepLinkHelper.open_android_deep_link` | Deep Links | android, routing | Opens Android deep links through Appium. |
| `DeepLinkHelper.open_universal_link` | Deep Links | universal links | Opens a universal link through the active mobile session. |
| `ClipboardHelper.set_text`, `get_text` | Clipboard | text | Reads and writes mobile clipboard text. |
| `assert_no_unlabeled_controls` | Accessibility | a11y, labels | Detects interactive controls without accessible labels in page source. |
| `find_unlabeled_controls` | Accessibility | a11y, diagnostics | Returns unlabeled control diagnostics. |
| `capture_screen_screenshot` | Visual | screenshot | Saves a screenshot to a controlled path. |
| `assert_screenshot_matches_baseline` | Visual | baseline | Byte-level screenshot baseline comparison. |
| `wait_until` | Wait | polling, async | Polls non-UI systems such as APIs, files, jobs, and email backends. |
| `extract_otp`, `extract_first_match` | Text | otp, regex | Extracts values from SMS/email/push text. |
| `normalize_text`, `extract_numbers` | Text | parsing | Stable text normalization and numeric extraction. |
| `random_email`, `random_username`, `random_phone` | Data | test data | Generates readable unique test data. |
| `unique_id`, `timestamped_value` | Data | uniqueness | Generates IDs and timestamped values. |
| `wait_for_file`, `assert_file_exists` | Files | downloads | Waits for and validates generated files. |
| `cleanup_directory` | Files | cleanup | Recreates a clean directory for artifacts/downloads. |
| `ApiClient` | API | setup, cleanup | Lightweight API client for mobile/API hybrid tests. |
| `assert_status_code`, `assert_json_field` | API | assertions | API response assertion helpers. |
| `SoftAssert`, `soft_assert` | Assertions | grouped failures | Collects multiple validation failures before failing. |
| `step`, `attach_text`, `attach_json` | Allure Debug | reporting | Adds reusable report steps and attachments. |
| `BaseScreen.tap` | Screen Actions | retry, verification | Retries failed taps and can verify expected post-tap state. |
| `BaseScreen.type_text` | Screen Actions | retry, verification, input | Types text and verifies the target value changed before continuing. |
| `BaseScreen.type_text_with_keyboard` | Screen Actions | ios, keyboard, secure fields | Types through the active iOS keyboard when `send_keys` is not enough. |

## Gestures

Allure debug attachments are written into `reports/allure-results`. The default framework report
then turns those results into the core product report at `reports/automation-report/index.html`;
official Allure HTML remains optional through `--report-kind allure` or `--report-kind both`.

```python
from utils.helpers.gestures import GestureHelper


def test_scrolls_to_bottom(mobile_driver):
    gestures = GestureHelper(mobile_driver)
    gestures.scroll_down()
    gestures.long_press(x=200, y=600)
```

## Contexts

Use this for hybrid apps that expose an in-app webview. It can also switch to mobile browser contexts when Appium exposes them as `CHROMIUM` or `WEBVIEW_*`. On iOS, it can use Appium's full context metadata to match by title, URL, or bundle id.

```python
from utils.helpers.contexts import ContextHelper


def test_webview(mobile_driver):
    contexts = ContextHelper(mobile_driver)
    contexts.switch_to_webview(title="Checkout", url_contains="/checkout")
    assert "WEBVIEW" in contexts.current_context()
    contexts.switch_to_native()
```

## Permissions

```python
from utils.helpers.permissions import PermissionHelper


def test_location_permission(mobile_driver):
    PermissionHelper(mobile_driver).grant_android_permission(
        "com.example.app",
        "android.permission.ACCESS_FINE_LOCATION",
    )
```

## Deep Links

```python
from utils.helpers.deep_links import DeepLinkHelper


def test_android_deep_link(mobile_driver):
    DeepLinkHelper(mobile_driver).open_android_deep_link(
        "example://orders/123",
        "com.example.app",
    )
```

## Accessibility

```python
from utils.helpers.accessibility import assert_no_unlabeled_controls


def test_accessibility_labels(mobile_driver):
    assert_no_unlabeled_controls(mobile_driver.page_source, platform="android")
```

## API Setup

```python
from utils.helpers.api import ApiClient, assert_status_code


def test_api_setup(api_client: ApiClient):
    response = api_client.get("/status")
    assert_status_code(response, 200)
```

## Test Data

```python
from utils.helpers.data import random_email, unique_id


email = random_email(domain="example.test")
order_id = unique_id("order")
```

## iOS Keyboard Typing

Use this for iOS secure fields or custom inputs where XCTest `send_keys` does not change the field
value. It configures the simulator keyboard to `en_US/QWERTY` and types through Appium's
`mobile: keys` extension.

```python
self.type_text_with_keyboard(self.password_field, "mypassword", clear_first=False, sensitive=True)
```

## Action Retries

Mobile actions retry independently from test-case reruns. `BaseScreen` retries actions three times
by default and verifies text entry before moving to the next action. This catches silent mobile
failures such as `send_keys` returning successfully while the field value stays unchanged.

```yaml
retries:
  action_default: 3
  action_delay_seconds: 0.3
```

`tap` also accepts an optional verification callback or locator:

```python
self.tap(self.login_button, "Login", verify=self.logged_in_message)
```

## Self-Healing Locators

Self-healing is supported through engineer-defined locator fallbacks, the same conservative model
used by the web framework.

```python
self.locator_with_fallbacks(
    "Login button",
    (AppiumBy.ACCESSIBILITY_ID, "loginBtn"),
    (AppiumBy.XPATH, "//*[@name='loginBtn' or @resource-id='loginBtn']"),
)
```

Runtime auto-healing is a separate source-based adapter and is disabled by default. Enable
`runtime_healing.mode: suggest` to audit ranked candidates without applying them, or `apply` only
after reviewing the audit trail and allowed actions. Audit events are written to
`reports/healing/events.jsonl`.
