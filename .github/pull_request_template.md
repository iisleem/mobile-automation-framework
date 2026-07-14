## What Changed

- 

## Why

- 

## Validation

- [ ] `python -m compileall -q framework.py conftest.py screens flows utils scripts tests`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `python framework.py run --helpers --no-open-report --no-generate-report`
- [ ] Device examples were run locally, or this PR does not affect device execution.
- [ ] Hybrid sample apps were built and run, or this PR does not affect hybrid execution.

## Notes

- Setup, secrets, capabilities, reports, and CI changes are documented.
