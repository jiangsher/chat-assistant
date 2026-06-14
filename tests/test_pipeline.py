from __future__ import annotations

import numpy as np

from recognize.capture.screen_capture import CapturedImage
from recognize.models.config import Region
from recognize.models.recognition_result import TextBlock
from recognize.recognition.pipeline import RecognitionPipeline
from recognize.recognition.unread_detector import UnreadDetector


class FakeCapture:
    def __init__(self, captured: CapturedImage) -> None:
        self.captured = captured
        self.calls = 0
        self.screen_calls = 0

    def capture(self, region: Region) -> CapturedImage:
        self.calls += 1
        assert region == self.captured.region
        return self.captured

    def capture_screen(self) -> CapturedImage:
        self.screen_calls += 1
        return self.captured


class FakeOcrEngine:
    def recognize(self, image: np.ndarray):
        _ = image
        return [
            TextBlock(text="张先生拓保软件|招聘主管", confidence=0.99, bbox=(114, 143, 330, 173)),
            TextBlock(text="18:04", confidence=0.99, bbox=(472, 145, 519, 172)),
            TextBlock(text="[送达]对这个岗位很感兴趣", confidence=0.99, bbox=(115, 189, 462, 211)),
        ]


def test_run_captured_reuses_existing_screenshot_without_capturing_again() -> None:
    region = Region(x=1, y=2, width=300, height=400)
    captured = CapturedImage(region=region, pixels=np.zeros((100, 100, 3), dtype=np.uint8))
    capture = FakeCapture(captured)
    pipeline = RecognitionPipeline(
        capture=capture,
        ocr_engine=FakeOcrEngine(),
        unread_detector=UnreadDetector(),
    )

    result = pipeline.run_captured(captured)

    assert capture.calls == 0
    assert result.region == region
    assert len(result.raw_text_blocks) == 3
    assert result.cards[0].name == "张先生"


def test_run_once_captures_then_uses_same_pipeline_path() -> None:
    region = Region(x=1, y=2, width=300, height=400)
    captured = CapturedImage(region=region, pixels=np.zeros((100, 100, 3), dtype=np.uint8))
    capture = FakeCapture(captured)
    pipeline = RecognitionPipeline(
        capture=capture,
        ocr_engine=FakeOcrEngine(),
        unread_detector=UnreadDetector(),
    )

    result = pipeline.run_once(region)

    assert capture.calls == 1
    assert result.region == region
    assert len(result.raw_text_blocks) == 3


def test_run_detected_from_captured_returns_detected_region_and_result(monkeypatch) -> None:
    region = Region(x=1, y=2, width=300, height=400)
    captured = CapturedImage(region=region, pixels=np.zeros((100, 100, 3), dtype=np.uint8))
    pipeline = RecognitionPipeline(
        capture=FakeCapture(captured),
        ocr_engine=FakeOcrEngine(),
        unread_detector=UnreadDetector(),
    )
    detected = type("Detected", (), {"region": region})()
    monkeypatch.setattr(
        "recognize.recognition.pipeline.detect_message_list_region",
        lambda *args, **kwargs: detected,
    )
    monkeypatch.setattr(
        "recognize.recognition.pipeline.crop_detected_region",
        lambda source, item: source,
    )

    result = pipeline.run_detected_from_captured(captured)

    assert result is not None
    actual_detected, recognition_result = result
    assert actual_detected is detected
    assert recognition_result.region == region
