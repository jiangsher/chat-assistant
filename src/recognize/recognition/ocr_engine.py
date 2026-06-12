from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from recognize.models.recognition_result import TextBlock


class OcrEngine(ABC):
    @abstractmethod
    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        raise NotImplementedError


class PlaceholderOcrEngine(OcrEngine):
    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        _ = image
        return []


class RapidOcrEngine(OcrEngine):
    def __init__(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise RuntimeError(
                "OCR 依赖未安装，请运行：.\\.venv\\Scripts\\python.exe -m pip install rapidocr-onnxruntime"
            ) from exc

        self.engine = RapidOCR()

    def recognize(self, image: np.ndarray) -> list[TextBlock]:
        results, _ = self.engine(image)
        if not results:
            return []

        text_blocks: list[TextBlock] = []
        for box, text, score in results:
            xs = [int(point[0]) for point in box]
            ys = [int(point[1]) for point in box]
            text_blocks.append(
                TextBlock(
                    text=str(text),
                    confidence=float(score),
                    bbox=(min(xs), min(ys), max(xs), max(ys)),
                )
            )

        return text_blocks
