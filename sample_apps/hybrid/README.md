# Hybrid Demo Sample Apps

This folder contains small real hybrid applications used by the framework examples:

- Android: native `Activity` hosting an Android `WebView`.
- iOS: native UIKit app hosting a `WKWebView`.

The apps render the same local HTML form and expose a real webview context to Appium. Binaries are
not committed. Build them locally into `apps/`:

```bash
python scripts/build_hybrid_sample_apps.py --all
```

Run the examples after Appium and a device/simulator are ready:

```bash
python framework.py run --hybrid-example --profile android_hybrid_demo
python framework.py run --hybrid-example --profile ios_hybrid_demo --device-name "iPhone 15"
```
