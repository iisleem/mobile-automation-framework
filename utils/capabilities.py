from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any


CLI_CAPABILITY_MAP = {
    "app": "appium:app",
    "device_name": "appium:deviceName",
    "platform_version": "appium:platformVersion",
    "udid": "appium:udid",
}


def resolve_capabilities(
    project_root: Path,
    capabilities_config: dict[str, Any],
    profile_name: str,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profiles = capabilities_config.get("profiles", {})
    if profile_name not in profiles:
        available = ", ".join(sorted(profiles))
        raise KeyError(f"Unknown capability profile '{profile_name}'. Available: {available}")

    capabilities = deepcopy(profiles[profile_name])
    _apply_overrides(capabilities, overrides or {})
    capabilities = _prune_empty_values(capabilities)
    _resolve_local_app_path(project_root, capabilities)
    return capabilities


def available_profiles(capabilities_config: dict[str, Any]) -> list[str]:
    return sorted(capabilities_config.get("profiles", {}))


def _apply_overrides(
    capabilities: dict[str, Any],
    overrides: dict[str, Any],
) -> None:
    for override_key, capability_key in CLI_CAPABILITY_MAP.items():
        value = overrides.get(override_key)
        if value:
            capabilities[capability_key] = value

    if overrides.get("no_reset") is not None:
        capabilities["appium:noReset"] = bool(overrides["no_reset"])
    if overrides.get("full_reset"):
        capabilities["appium:fullReset"] = True
        capabilities["appium:noReset"] = False


def _prune_empty_values(capabilities: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in capabilities.items() if value is not None and value != ""}


def _resolve_local_app_path(project_root: Path, capabilities: dict[str, Any]) -> None:
    app_value = capabilities.get("appium:app")
    if not app_value or "://" in str(app_value):
        return

    app_path = Path(str(app_value)).expanduser()
    if not app_path.is_absolute():
        app_path = project_root / app_path
    capabilities["appium:app"] = str(app_path)
