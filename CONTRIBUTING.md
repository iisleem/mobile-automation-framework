# Contributing

Keep framework changes focused, mobile-specific, and testable.

- Put UI details in `screens/`, not in test files.
- Put reusable business journeys in `flows/`.
- Add helper unit tests under `tests/helpers/` for new utility behavior.
- Add or update examples when a feature changes how users write tests.
- Avoid hardcoding device names, app paths, credentials, or platform versions in tests.
- Keep this repository independent from web automation projects. Shared utilities are welcome only
  when they are useful to mobile automation setup, cleanup, or assertions.

## Local Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

## Validation

Run the fast checks before opening a pull request:

```bash
python -m compileall -q framework.py conftest.py screens flows utils scripts tests
ruff check .
python framework.py run --helpers --no-open-report --no-generate-report
```

Run device examples locally when a change affects Appium sessions, capabilities, screen objects, or
mobile web behavior:

```bash
python framework.py run --android-example --profile android_the_app --no-open-report
python framework.py run --ios-example --profile ios_the_app --no-open-report
python framework.py run --mobile-web --profile android_mobile_web --no-open-report
python framework.py run --mobile-web --profile ios_mobile_web --no-open-report
```

## Pull Requests

Each PR should explain:

- What changed.
- Why the change belongs in the mobile framework.
- How it was validated.
- Whether it affects setup, secrets, capabilities, reports, or CI.
