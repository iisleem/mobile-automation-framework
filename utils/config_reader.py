from __future__ import annotations

from pathlib import Path
from typing import Any

from automation_core.config import ConfigReader as CoreConfigReader


class ConfigReader(CoreConfigReader):
    def __init__(self, project_root: Path | str) -> None:
        super().__init__(project_root)

    def read_capabilities(self) -> dict[str, Any]:
        return self.read_yaml("config/capabilities.yaml")

    def load(self, environment: str) -> dict[str, Any]:
        return super().load(
            environment,
            environment_key="environment",
            environment_config_key="environment_config",
            merge_environment=False,
        )
