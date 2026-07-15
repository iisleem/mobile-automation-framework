# Mobile Framework Walkthrough

This walkthrough shows a first-run path for a new mobile suite: validate the framework without a
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
```

The default report is the automation-core product report. It summarizes the run, profiles,
environments, devices, pass rate, slow tests, failure summary, and history trends. Open
`reports/automation-report/index.html` locally after generation, or omit `--no-open` when you want
the CLI to open the report automatically. The same generation writes a report gallery to
`reports/automation-report/reports.html` and stores structured run summary, timeline, and signal
data under `reports/automation-report/runs/<timestamp>-<run-id>/`.

Use the dashboard to check run status first, then drill into test details for step timing, action
attempts, retry notes, and artifact links. The raw result stream remains in `reports/allure-results`
so the core report and optional official Allure report can be regenerated from the same run data.

![Core report overview](assets/walkthrough/core-report-overview.png)

For the maintained screenshot inventory, see [SCREENSHOTS.md](SCREENSHOTS.md).

Use these report kinds when needed:

```bash
python framework.py report generate --report-kind core --no-open
python framework.py report generate --report-kind allure --no-open
python framework.py report generate --report-kind both --no-open
python framework.py report generate --report-kind summary --no-open
```

## 3. Run Android And iOS Samples

Start Appium in a separate terminal. The command does not require `sudo` when Appium and its drivers
are installed in your user-managed Node environment:

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

Choose an iOS simulator before running iOS samples. `--device-name` can work on a simple machine,
but `--udid` avoids ambiguity when multiple simulators have the same name and prevents Appium from
choosing or cloning a simulator you did not intend to use:

```bash
xcrun simctl list devices available
xcrun simctl boot <UDID>
xcrun simctl bootstatus <UDID> -b
```

Prefix the `xcrun` commands with `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer` when
your shell needs the full Xcode toolchain.

Run iOS with a full Xcode developer directory when `xcode-select` points at Command Line Tools:

```bash
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
python framework.py run --ios-example --profile ios_the_app --udid <UDID> --no-open-report
```

On failures the framework captures screenshots, page source, logs, and optional recordings according
to `config/settings.yaml`. This Android artifact came from a real sample run where a system overlay
interrupted the first attempt and the test passed on retry:

![Android retry artifact](assets/walkthrough/android-retry-artifact.png)

Action-level retries validate that each sensitive mobile action actually completed before the next
step continues. Test-level retries rerun the whole test, so a passed run can still leave useful
artifacts from an earlier failed attempt.

## 4. Run Hybrid And Mobile Web Samples

Build the local hybrid fixtures:

```bash
python scripts/build_hybrid_sample_apps.py --all
```

Run hybrid profiles:

```bash
python framework.py run --hybrid-example --profile android_hybrid_demo --no-open-report
python framework.py run --hybrid-example --profile ios_hybrid_demo --udid <UDID> --no-open-report
```

Run mobile web profiles:

```bash
python framework.py run --mobile-web --profile android_mobile_web --no-open-report
python framework.py run --mobile-web --profile ios_mobile_web --udid <UDID> --no-open-report
```

Hybrid tests use `ContextHelper` to move between `NATIVE_APP` and webview contexts. Native profiles
do not enable webview discovery by default; hybrid profiles do. Mobile context switching is timing
sensitive: wait for the app screen first, then switch to the webview or browser context, and switch
back to native before checking native navigation or system UI.

## 5. Find Artifacts

The default artifact locations are:

- `reports/automation-report/index.html` for the core product report.
- `reports/automation-report/reports.html` for choosing a retained run.
- `reports/automation-report/runs/<timestamp>-<run-id>/report-data.json` for structured report data.
- `reports/allure-results` for raw test result files and attachments.
- `screenshots` for failure screenshots.
- `source_dumps` for page source captured on failure.
- `logs` for device and framework logs.
- `recordings` for optional video artifacts when recording is enabled.
- `reports/healing/events.jsonl` for runtime healing audit events when suggest/apply mode is enabled.

The report links back to attachments from the result stream. The filesystem folders are still useful
when debugging a device locally or attaching one failed attempt to a ticket.

## 6. Start A Product Suite

Use the starter project when creating a product-specific suite:

```bash
cp -R templates/starter_project ../my-mobile-suite
cd ../my-mobile-suite
```

The starter keeps product screens, flows, and tests separate from framework internals. Keep shared,
environment-neutral helpers in `automation-core`; keep Appium screens, capabilities, and
device-specific behavior in the mobile suite.
