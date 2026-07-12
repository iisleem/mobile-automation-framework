# Troubleshooting

## Appium Server Is Not Reachable

Start Appium with the same base path used by the framework:

```bash
appium --base-path /
```

The default server URL is `http://127.0.0.1:4723` in `config/settings.yaml`. You can override it:

```bash
python framework.py run --profile android_the_app --appium-server http://127.0.0.1:4723
```

## Appium Drivers Are Missing

Install the Android and iOS drivers:

```bash
appium driver install uiautomator2
appium driver install xcuitest
appium driver list --installed
```

## Android Device Is Not Detected

Confirm that `adb` sees a booted device:

```bash
adb devices
adb shell getprop sys.boot_completed
```

If `adb` is not found, add Android platform tools to your `PATH`.

## Android Chrome Mobile Web Fails To Start

Mobile web profiles use Chrome through Appium. Start Appium with chromedriver autodownload enabled
when the emulator Chrome version does not match a local chromedriver:

```bash
appium --base-path / --allow-insecure '*:chromedriver_autodownload'
```

## iOS Simulator Tools Are Not Found

Install full Xcode and point commands at its developer directory:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer xcrun simctl list devices
```

If `xcode-select -p` points to Command Line Tools, either switch globally:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

or prefix iOS run commands with `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`.

## WebDriverAgent Stays Running After iOS Tests

If an iOS run is interrupted, stop stale WebDriverAgent build processes and shut down the simulator:

```bash
pkill -f 'appium-webdriveragent/WebDriverAgent.xcodeproj' || true
xcrun simctl shutdown all
```

## iOS Secure Fields Do Not Receive Text

Use `BaseScreen.type_text_with_keyboard(..., sensitive=True)` for secure fields or inputs where
normal `send_keys` returns without changing the field value. The iOS profiles also disable hardware
keyboard mode and force the simulator software keyboard.

## Sample Apps Are Missing

The native examples download TheApp automatically when the fixture is missing. You can download
fixtures manually:

```bash
python scripts/download_sample_apps.py --all
```

Sample app binaries are ignored by git. They should not be committed to the repository.

## Reports Do Not Open Locally

CI and server-like environments skip report auto-opening. Generate or open reports manually:

```bash
python framework.py report generate
python framework.py report open
```

If the Allure CLI is not installed, the framework generates a built-in HTML fallback report.

## GitHub Actions Does Not Run Device Tests

The default CI workflow runs helper/unit tests and static checks only. Real Android/iOS runs need
Appium, emulators or simulators, Xcode for iOS, and device-specific setup. Run device examples
locally or add a self-hosted runner when you want pipeline device execution.
