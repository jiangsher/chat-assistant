from __future__ import annotations

from recognize.capture.screen_capture import CapturedImage, ScreenCapture
from recognize.models.config import Region
from recognize.models.recognition_result import RecognitionResult
from recognize.recognition.ocr_engine import OcrEngine
from recognize.recognition.parser import parse_candidate_cards
from recognize.recognition.unread_detector import UnreadDetector


class RecognitionPipeline:
    def __init__(
        self,
        capture: ScreenCapture,
        ocr_engine: OcrEngine,
        unread_detector: UnreadDetector,
    ) -> None:
        self.capture = capture
        self.ocr_engine = ocr_engine
        self.unread_detector = unread_detector

    def run_once(self, region: Region) -> RecognitionResult:
        captured = self.capture.capture(region)
        return self.run_captured(captured)

    def run_captured(self, captured: CapturedImage) -> RecognitionResult:
        text_blocks = self.ocr_engine.recognize(captured.pixels)
        cards = parse_candidate_cards(
            text_blocks,
            captured.pixels,
            badge_reader=self._read_badge_text,
        )

        return RecognitionResult(
            region=captured.region,
            cards=cards,
            raw_text_blocks=text_blocks,
        )

    def _read_badge_text(self, image) -> str | None:
        import cv2

        if image.size == 0:
            return None

        enlarged = cv2.resize(image, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        blocks = self.ocr_engine.recognize(enlarged)
        digits = "".join(char for block in blocks for char in block.text if char.isdigit())
        return digits or None
