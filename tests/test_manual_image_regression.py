from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from manual_case_data import MANUAL_CASES, unread_contact_total, unread_total
from recognize.recognition.card_labels import title_label_for_card
from recognize.recognition.ocr_engine import RapidOcrEngine
from recognize.recognition.parser import detect_app_template, parse_candidate_cards


ASSET_DIR = Path(__file__).resolve().parents[1] / "test_assets" / "manual_cases"


@pytest.fixture(scope="module")
def ocr_engine() -> RapidOcrEngine:
    return RapidOcrEngine()


@pytest.mark.parametrize("filename,case", sorted(MANUAL_CASES.items()))
def test_manual_case_images_parse_expected_unread_cards(
    filename: str,
    case: dict[str, object],
    ocr_engine: RapidOcrEngine,
) -> None:
    image = load_image(ASSET_DIR / filename)
    blocks = ocr_engine.recognize(image)

    assert detect_app_template(blocks) == case["template"]

    cards = parse_candidate_cards(blocks, image, badge_reader=badge_reader(ocr_engine))
    unread_cards = [card for card in cards if card.unread]
    expected_unread = [
        card for card in case["cards"] if isinstance(card, dict) and card["unread"]
    ]

    assert len(cards) == len(case["cards"])
    assert len(unread_cards) == unread_contact_total(case)
    assert sum(int(card.unread_badge or 0) for card in unread_cards) == unread_total(case)

    actual_by_name = {normalize(card.name): card for card in unread_cards}
    for expected in expected_unread:
        expected_name = normalize(str(expected["name"]))
        assert expected_name in actual_by_name
        actual = actual_by_name[expected_name]
        assert actual.unread_badge == expected["unread"]
        assert normalize(actual.title) == normalize(str(expected["title"]))
        assert normalize(actual.summary) == normalize(str(expected["summary"]))
        assert normalize(actual.time or "") == normalize(str(expected["time"]))
        assert title_label_for_card(actual) == case["title_label"]


def load_image(path: Path) -> np.ndarray:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise AssertionError(f"Failed to load image: {path}")
    return image


def badge_reader(ocr_engine: RapidOcrEngine):
    def read_badge(image: np.ndarray) -> str | None:
        enlarged = cv2.resize(image, None, fx=8, fy=8, interpolation=cv2.INTER_CUBIC)
        blocks = ocr_engine.recognize(enlarged)
        digits = "".join(char for block in blocks for char in block.text if char.isdigit())
        return digits or None

    return read_badge


def normalize(value: str) -> str:
    return "".join(value.split())
