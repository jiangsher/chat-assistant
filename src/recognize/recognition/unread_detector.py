from __future__ import annotations

import cv2
import numpy as np


class UnreadDetector:
    def __init__(self, min_red_pixels: int = 16) -> None:
        self.min_red_pixels = min_red_pixels

    def has_red_unread_marker(self, image: np.ndarray) -> bool:
        if image.size == 0:
            return False

        bgr = image[:, :, :3]
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        lower_red_1 = np.array([0, 80, 80])
        upper_red_1 = np.array([10, 255, 255])
        lower_red_2 = np.array([170, 80, 80])
        upper_red_2 = np.array([180, 255, 255])

        mask_1 = cv2.inRange(hsv, lower_red_1, upper_red_1)
        mask_2 = cv2.inRange(hsv, lower_red_2, upper_red_2)
        red_pixels = int(np.count_nonzero(mask_1 | mask_2))

        return red_pixels >= self.min_red_pixels

