# Mobile Framework Walkthrough

This walkthrough shows the first run path for a new mobile suite: validate the framework without a
device, generate the core product report, then move to Android, iOS, hybrid, or mobile web profiles
when Appium and devices are ready.

## 1. Install And Validate

```bash
cd mobile-automation-framework
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
python framework.py doctor
python framework.py run --helpers --no-open-report
```

The helper suite is device-free. Use it to confirm config loading, retries, waits, assertions,
reporting, and reusable helpers before connecting Appium.

## 2. Review The Core Report

Generate or refresh the default report:

```bash
python framework.py report generate --no-open
open reports/automation-report/index.html
```

The default report is the automation-core product report. It summarizes the run, profiles,
environments, devices, pass rate, slow tests, failure summary, and history trends.

![Core report overview](assets/walkthrough/core-report-overview.png)

Use these report kinds when needed:

```bash
python framework.py report generate --report-kind core --no-open
python framework.py report generate --report-kind allure --no-open
python framework.py report generate --report-kind both --no-open
python framework.py report generate --report-kind summary --no-open
```

## 3. Run Android And iOS Samples

Start Appium in a separate terminal:

```bash
appium --base-path /
```

Prepare sample app fixtures:

```bash
python scripts/download_sample_apps.py --all
```

Run Android:

```bash
python framework.py run --android-example --profile android_the_app --no-open-report
```

Run iOS:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
python framework.py run --ios-example --profile ios_the_app --device-name "iPhone 16" --no-open-report
```

On failures the framework captures screenshots, page source, logs, and optional recordings according
to `config/settings.yaml`. Action-level retries validate that each sensitive mobile action actually
completed before the next step continues; test-level retries still handle full-test flakiness.

## 4. Run Hybrid And Mobile Web Samples

Build the local hybrid fixtures:

```bash
python scripts/build_hybrid_sample_apps.py --all
```

Run hybrid profiles:

```bash
python framework.py run --hybrid-example --profile android_hybrid_demo --no-open-report
python framework.py run --hybrid-example --profile ios_hybrid_demo --device-name "iPhone 16" --no-open-report
```

Run mobile web profiles:

```bash
python framework.py run --mobile-web --profile android_mobile_web --no-open-report
python framework.py run --mobile-web --profile ios_mobile_web --device-name "iPhone 16" --no-open-report
```

Hybrid tests use `ContextHelper` to move between `NATIVE_APP` and webview contexts. Native profiles
do not enable webview discovery by default; hybrid profiles do.

## 5. Start A Product Suite

Use the starter project when creating a product-specific suite:

```bash
cp -R templates/starter_project ../my-mobile-suite
cd ../my-mobile-suite
```

The starter keeps product screens, flows, and tests separate from framework internals. Keep shared,
environment-neutral helpers in `automation-core`; keep Appium screens, capabilities, and
device-specific behavior in the mobile suite.
