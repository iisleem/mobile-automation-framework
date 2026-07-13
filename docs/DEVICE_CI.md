# Device CI

The default hosted workflow validates the framework without devices. Real Android and iOS execution
needs Appium plus an emulator, simulator, real device, or device farm. This repo includes a manual
workflow for that path: `.github/workflows/device-examples.yml`.

## Self-Hosted Runner

Recommended runner labels:

```text
self-hosted, mobile
```

Install on the runner:

- Python 3.11+
- Node.js and npm
- Appium 2
- Appium drivers: `uiautomator2`, `xcuitest`
- Android SDK and platform tools for Android
- Full Xcode for iOS simulator runs

Start the workflow from GitHub Actions and choose one suite:

- `android-native`
- `ios-native`
- `android-mobile-web`
- `ios-mobile-web`
- `android-hybrid`
- `ios-hybrid`
- `matrix`

The workflow accepts optional `device_name`, `platform_version`, and `udid` inputs. Set
`start_appium=true` when the runner should start a local Appium server for the job.

## Device Farm

Most device farms expose an Appium-compatible server URL plus credentials and provider-specific
capabilities. Store credentials as GitHub Secrets and pass the remote Appium endpoint through the
`appium_server` workflow input.

Keep provider-only capabilities in a separate local or CI-specific capability profile, for example:

```yaml
profiles:
  android_device_farm:
    platformName: Android
    appium:automationName: UiAutomator2
    appium:deviceName: "${DEVICE_NAME:-Google Pixel}"
    appium:platformVersion: "${ANDROID_VERSION:-15}"
    appium:app: "${DEVICE_FARM_APP:-}"
```

Do not commit device farm keys, access tokens, private app URLs, or signing secrets.

## Hybrid Examples In CI

Hybrid examples build local sample apps before execution:

```bash
python scripts/build_hybrid_sample_apps.py --android
python scripts/build_hybrid_sample_apps.py --ios
```

The generated files land in `apps/` and are gitignored.
