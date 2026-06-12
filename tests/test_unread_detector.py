import numpy as np

from recognize.models.config import Region
from recognize.models.recognition_result import CandidateCard, RecognitionResult
from recognize.recognition.unread_detector import UnreadDetector


def test_red_marker_detection() -> None:
    image = np.zeros((20, 20, 3), dtype=np.uint8)
    image[4:10, 4:10] = [0, 0, 255]

    assert UnreadDetector(min_red_pixels=10).has_red_unread_marker(image)


def test_red_marker_detection_returns_false_for_empty_image() -> None:
    image = np.zeros((0, 0, 3), dtype=np.uint8)

    assert not UnreadDetector().has_red_unread_marker(image)


def test_recognition_result_unread_count_sums_badges() -> None:
    result = RecognitionResult(
        region=Region(),
        cards=[
            CandidateCard(id="1", unread=True, unread_badge="3"),
            CandidateCard(id="2", unread=True, unread_badge="2"),
            CandidateCard(id="3", unread=False),
        ],
    )

    assert result.unread_count == 5
    assert result.unread_contact_count == 2
