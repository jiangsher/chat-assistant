from __future__ import annotations

import json
from pathlib import Path

from recognize.models.config import AppConfig, default_config_path


class ConfigStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def default(cls) -> "ConfigStore":
        return cls(default_config_path())

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig()

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(data)

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            config.model_dump_json(indent=2),
            encoding="utf-8",
        )

