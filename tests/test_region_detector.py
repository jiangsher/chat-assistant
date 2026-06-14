from __future__ import annotations

import numpy as np

from recognize.capture.screen_capture import CapturedImage
from recognize.models.config import Region
from recognize.models.recognition_result import TextBlock
from recognize.recognition.region_detector import crop_detected_region
from recognize.recognition.region_detector import detect_message_list_region
from recognize.recognition.region_detector import _generate_candidates


class FakeOcrEngine:
    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        height, width = image.shape[:2]
        if width < 300 or height < 300:
            return []
        return [
            TextBlock(text="Anna Chen", confidence=0.99, bbox=(100, 80, 220, 110)),
            TextBlock(text="10:20", confidence=0.99, bbox=(340, 80, 390, 110)),
            TextBlock(text="Product Designer", confidence=0.99, bbox=(100, 118, 260, 145)),
            TextBlock(
                text="Thanks for connecting, can we talk tomorrow?",
                confidence=0.99,
                bbox=(100, 150, 430, 175),
            ),
            TextBlock(text="Sofia Wang", confidence=0.99, bbox=(100, 230, 220, 260)),
            TextBlock(text="Mon", confidence=0.99, bbox=(340, 230, 390, 260)),
            TextBlock(text="Recruiter", confidence=0.99, bbox=(100, 268, 210, 295)),
            TextBlock(
                text="New opening: AI workflow specialist.",
                confidence=0.99,
                bbox=(100, 300, 410, 325),
            ),
        ]


class SelfWindowOcrEngine:
    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        _ = image
        return [
            TextBlock(text="聊天助手", confidence=0.99, bbox=(20, 20, 120, 50)),
            TextBlock(text="自动识别", confidence=0.99, bbox=(20, 60, 120, 90)),
        ]


def test_detect_message_list_region_scores_candidate_with_cards() -> None:
    image = np.full((620, 900, 3), 245, dtype=np.uint8)
    image[50:540, 220:680] = 255
    image[70:90, 245:265] = (50, 50, 245)
    captured = CapturedImage(region=Region(x=10, y=20, width=900, height=620), pixels=image)

    detected = detect_message_list_region(captured, FakeOcrEngine())

    assert detected is not None
    assert detected.region.is_valid
    assert detected.region.x >= 10
    assert detected.region.y >= 20
    assert "cards=" in detected.reason


def test_gray_badges_create_narrow_left_list_candidate() -> None:
    image = np.full((720, 1200, 3), 248, dtype=np.uint8)
    image[:, :410] = 242
    image[:, 410:414] = 225
    for y in (120, 220, 360):
        cv2_circle(image, 350, y, 15, (180, 180, 180))
    image[95:118, 520:580] = (220, 220, 220)

    candidates = _generate_candidates(image)

    assert candidates[0].reason == "gray-badges"
    assert 0 <= candidates[0].x <= 30
    assert candidates[0].width <= 430


def test_vertical_panel_candidate_can_cover_wide_left_list() -> None:
    image = np.full((720, 1400, 3), 248, dtype=np.uint8)
    image[:, :660] = 255
    image[:, 660:664] = 205
    image[:, 664:] = 246
    for y in (80, 180, 300, 420):
        cv2_circle(image, 80, y, 28, (220, 220, 220))

    candidates = _generate_candidates(image)

    wide_panels = [
        candidate
        for candidate in candidates
        if candidate.reason == "vertical-panel" and 640 <= candidate.width <= 690
    ]
    assert wide_panels


def test_detect_message_list_region_ignores_self_window_text() -> None:
    image = np.full((500, 700, 3), 255, dtype=np.uint8)
    captured = CapturedImage(region=Region(x=0, y=0, width=700, height=500), pixels=image)

    detected = detect_message_list_region(captured, SelfWindowOcrEngine())

    assert detected is None


def test_crop_detected_region_returns_screen_relative_crop() -> None:
    image = np.zeros((100, 120, 3), dtype=np.uint8)
    captured = CapturedImage(region=Region(x=50, y=60, width=120, height=100), pixels=image)
    detected_region = Region(x=70, y=90, width=30, height=20)

    cropped = crop_detected_region(
        captured,
        detected=type("Detected", (), {"region": detected_region})(),
    )

    assert cropped.region == detected_region
    assert cropped.pixels.shape[:2] == (20, 30)


def cv2_circle(
    image: np.ndarray,
    x: int,
    y: int,
    radius: int,
    color: tuple[int, int, int],
) -> None:
    import cv2

    cv2.circle(image, (x, y), radius, color, -1)
