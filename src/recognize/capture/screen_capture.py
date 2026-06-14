from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from recognize.models.config import Region


@dataclass(frozen=True)
class CapturedImage:
    region: Region
    pixels: np.ndarray


class ScreenCapture:
    def capture_screen(self, monitor_index: int = 1) -> CapturedImage:
        try:
            import mss
        except ImportError as exc:
            raise RuntimeError("mss is required for screen capture") from exc

        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor_index >= len(monitors):
                monitor_index = 1
            monitor = monitors[monitor_index]
            image = np.array(sct.grab(monitor))

        region = Region(
            x=int(monitor["left"]),
            y=int(monitor["top"]),
            width=int(monitor["width"]),
            height=int(monitor["height"]),
        )
        return CapturedImage(region=region, pixels=image)

    def capture(self, region: Region) -> CapturedImage:
        try:
            import mss
        except ImportError as exc:
            raise RuntimeError("mss is required for screen capture") from exc

        monitor = {
            "left": region.x,
            "top": region.y,
            "width": region.width,
            "height": region.height,
        }

        with mss.mss() as sct:
            image = np.array(sct.grab(monitor))

        return CapturedImage(region=region, pixels=image)
