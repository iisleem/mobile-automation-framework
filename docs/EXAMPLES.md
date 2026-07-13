# Examples

These examples show the main ways a team can use the framework.

## Android Native

```bash
python framework.py run --android-example --profile android_the_app --no-open-report
```

```python
from flows.the_app import TheAppLoginFlow


def test_android_login(mobile_driver):
    TheAppLoginFlow(mobile_driver).login_successfully()
```

## iOS Native

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
python framework.py run --ios-example --profile ios_the_app --device-name "iPhone 16" --no-open-report
```

## Hybrid App

Build the sample apps first:

```bash
python scripts/build_hybrid_sample_apps.py --all
```

Run Android or iOS hybrid:

```bash
python framework.py run --hybrid-example --profile android_hybrid_demo --no-open-report
python framework.py run --hybrid-example --profile ios_hybrid_demo --device-name "iPhone 16" --no-open-report
```

The test starts in native context, switches to the webview, interacts with CSS selectors, then
switches back to native:

```python
from screens.hybrid import HybridNativeScreen, HybridWebScreen
from utils.helpers.contexts import ContextHelper


def test_hybrid_demo(mobile_driver):
    native = HybridNativeScreen(mobile_driver)
    native.expect_loaded()

    contexts = ContextHelper(mobile_driver)
    contexts.switch_to_webview(title="Hybrid Demo", url_contains="hybrid.demo.local")

    web = HybridWebScreen(mobile_driver)
    web.submit_name("Hybrid QA")
    web.expect_greeting("Hybrid QA")

    contexts.switch_to_native()
    native.expect_loaded()
```

Android normally exposes a `WEBVIEW_*` or `CHROMIUM` context for this sample. iOS hybrid profiles
enable full webview discovery and the helper can match by context metadata. If the local Web
Inspector/Appium/Xcode combination still exposes only `NATIVE_APP`, the example skips with a clear
message.

## Mobile Web

```bash
python framework.py run --mobile-web --profile android_mobile_web --no-open-report
python framework.py run --mobile-web --profile ios_mobile_web --device-name "iPhone 16" --no-open-report
```

## Deep Links

```python
from utils.helpers.deep_links import DeepLinkHelper


def test_opens_order_details(mobile_driver):
    DeepLinkHelper(mobile_driver).open_android_deep_link(
        "example://orders/123",
        "com.example.app",
    )
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

## Device Matrix

```bash
python framework.py run --profiles android_the_app android_mobile_web --profile-workers 2 --no-open-report
```
