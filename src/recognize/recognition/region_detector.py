from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import cv2
import numpy as np

from recognize.capture.screen_capture import CapturedImage
from recognize.models.config import Region
from recognize.models.recognition_result import TextBlock
from recognize.recognition.parser import parse_candidate_cards


SELF_WINDOW_WORDS = (
    "聊天助手",
    "识别助手",
    "选择区域",
    "自动识别",
    "刷新",
    "复制",
    "调试",
    "Codex",
)


@dataclass(frozen=True)
class DetectedRegion:
    region: Region
    score: float
    reason: str


@dataclass(frozen=True)
class _CandidateRegion:
    x: int
    y: int
    width: int
    height: int
    visual_score: float
    reason: str

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class _OcrEngineLike:
    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        raise NotImplementedError


def detect_message_list_region(
    captured: CapturedImage,
    ocr_engine: _OcrEngineLike,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
) -> DetectedRegion | None:
    image = _ensure_bgr(captured.pixels)
    candidates = _generate_candidates(image)
    best: DetectedRegion | None = None

    for candidate in candidates[:8]:
        crop = _crop(image, candidate)
        if crop.size == 0:
            continue

        blocks = ocr_engine.recognize(crop)
        if _contains_self_window_text(blocks):
            continue

        cards = parse_candidate_cards(blocks, crop, badge_reader)
        if not cards:
            continue

        unread_contacts = sum(1 for card in cards if card.unread)
        unread_messages = sum(
            int(card.unread_badge)
            if card.unread and card.unread_badge and card.unread_badge.isdigit()
            else 1
            for card in cards
            if card.unread
        )
        time_count = sum(1 for card in cards if card.time)
        title_count = sum(1 for card in cards if card.title)
        score = (
            candidate.visual_score
            + len(cards) * 12
            + unread_contacts * 6
            + unread_messages * 0.8
            + time_count * 2
            + title_count
        )
        detected = DetectedRegion(
            region=Region(
                x=captured.region.x + candidate.x,
                y=captured.region.y + candidate.y,
                width=candidate.width,
                height=candidate.height,
            ),
            score=score,
            reason=f"{candidate.reason}; cards={len(cards)} unread={unread_contacts}",
        )
        if best is None or detected.score > best.score:
            best = detected

    if best is None or best.score < 16:
        return None
    return best


def crop_detected_region(captured: CapturedImage, detected: DetectedRegion) -> CapturedImage:
    x0 = max(0, detected.region.x - captured.region.x)
    y0 = max(0, detected.region.y - captured.region.y)
    x1 = min(captured.pixels.shape[1], x0 + detected.region.width)
    y1 = min(captured.pixels.shape[0], y0 + detected.region.height)
    return CapturedImage(
        region=detected.region,
        pixels=captured.pixels[y0:y1, x0:x1].copy(),
    )


def _ensure_bgr(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def _generate_candidates(image: np.ndarray) -> list[_CandidateRegion]:
    height, width = image.shape[:2]
    candidates: list[_CandidateRegion] = []

    def add(x: int, y: int, w: int, h: int, visual_score: float, reason: str) -> None:
        x = max(0, min(x, width - 1))
        y = max(0, min(y, height - 1))
        w = min(w, width - x)
        h = min(h, height - y)
        if w < 240 or h < 220:
            return
        item = _CandidateRegion(x, y, w, h, visual_score, reason)
        if not any(_iou(item.bbox, existing.bbox) > 0.92 for existing in candidates):
            candidates.append(item)

    red_regions = _red_badge_regions(image)
    if red_regions:
        x0 = min(region[0] for region in red_regions)
        y0 = min(region[1] for region in red_regions)
        x1 = max(region[2] for region in red_regions)
        y1 = max(region[3] for region in red_regions)
        add(
            x0 - 180,
            y0 - 90,
            min(760, max(420, x1 - x0 + 520)),
            min(height - max(0, y0 - 90), max(360, y1 - y0 + 180)),
            12 + len(red_regions) * 2,
            "red-badges",
        )

    panel_candidates = _light_panel_regions(image)
    for x, y, w, h, score in panel_candidates[:5]:
        add(x, y, w, h, score, "light-panel")

    add(0, 0, min(width, max(420, round(width * 0.42))), height, 3, "left-band")
    add(round(width * 0.28), 0, min(width, round(width * 0.48)), height, 2, "center-band")
    add(round(width * 0.52), 0, width - round(width * 0.52), height, 2, "right-band")
    add(0, 0, width, height, 1, "full-screen")

    candidates.sort(key=lambda item: item.visual_score, reverse=True)
    return candidates


def _red_badge_regions(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, (0, 70, 120), (12, 255, 255))
    mask2 = cv2.inRange(hsv, (165, 70, 120), (180, 255, 255))
    mask = cv2.bitwise_or(mask1, mask2)
    components, _, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    regions: list[tuple[int, int, int, int]] = []
    for index in range(1, components):
        x, y, w, h, area = stats[index]
        if 20 <= area <= 2600 and 8 <= w <= 80 and 8 <= h <= 80:
            regions.append((int(x), int(y), int(x + w), int(y + h)))
    return regions


def _light_panel_regions(image: np.ndarray) -> list[tuple[int, int, int, int, float]]:
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 215), (180, 55, 255))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (13, 13))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[tuple[int, int, int, int, float]] = []
    image_area = image.shape[0] * image.shape[1]
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < image_area * 0.08 or w < 260 or h < 260:
            continue
        ratio = h / max(w, 1)
        score = 4 + min(4, ratio)
        regions.append((x, y, w, h, score))
    regions.sort(key=lambda item: item[4] * item[2] * item[3], reverse=True)
    return regions


def _crop(image: np.ndarray, candidate: _CandidateRegion) -> np.ndarray:
    return image[
        candidate.y : candidate.y + candidate.height,
        candidate.x : candidate.x + candidate.width,
    ]


def _contains_self_window_text(blocks: list[TextBlock]) -> bool:
    text = " ".join(block.text for block in blocks if block.text)
    return any(word in text for word in SELF_WINDOW_WORDS)


def _iou(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = (ax1 - ax0) * (ay1 - ay0)
    area_b = (bx1 - bx0) * (by1 - by0)
    return inter / max(area_a + area_b - inter, 1)
