from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class Region(BaseModel):
    x: int = 0
    y: int = 0
    width: int = 360
    height: int = 800

    @property
    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0


class AppConfig(BaseModel):
    refresh_interval_ms: int = Field(default=10000, ge=500, le=60000)
    always_on_top: bool = True
    debug_mode: bool = False
    selected_region: Region | None = None
    window_x: int = 80
    window_y: int = 80
    window_width: int = 520
    window_height: int = 680


def default_config_path() -> Path:
    return Path.cwd() / "data" / "config.json"
