from __future__ import annotations

import os
from pathlib import Path
import re
from typing import Any

import yaml


ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


class ConfigReader:
    def __init__(self, project_root: Path | str) -> None:
        self.project_root = Path(project_root)

    def read_settings(self) -> dict[str, Any]:
        return self._read_yaml("config/settings.yaml")

    def read_environments(self) -> dict[str, Any]:
        return self._read_yaml("config/environments.yaml")

    def read_capabilities(self) -> dict[str, Any]:
        return self._interpolate_env(self._read_yaml("config/capabilities.yaml"))

    def load(self, environment: str) -> dict[str, Any]:
        settings = self.read_settings()
        environments = self.read_environments()
        if environment not in environments:
            available = ", ".join(sorted(environments))
            raise KeyError(f"Unknown environment '{environment}'. Available: {available}")

        return {
            **settings,
            "environment": environment,
            "environment_config": environments[environment],
        }

    def _read_yaml(self, relative_path: str) -> dict[str, Any]:
        path = self.project_root / relative_path
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            raise ValueError(f"Expected mapping in {path}")
        return data

    def _interpolate_env(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._interpolate_env(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._interpolate_env(item) for item in value]
        if not isinstance(value, str):
            return value

        def replace(match: re.Match[str]) -> str:
            env_name = match.group(1)
            default = match.group(2)
            return os.getenv(env_name, default if default is not None else "")

        return ENV_PATTERN.sub(replace, value)
