from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pydantic import BaseModel, Field

from recognize.models.config import Region


class TextBlock(BaseModel):
    text: str
    confidence: float = 0.0
    bbox: tuple[int, int, int, int]


class CandidateCard(BaseModel):
    id: str
    name: str = ""
    title: str = ""
    title_label: str = ""
    summary: str = ""
    time: str | None = None
    unread: bool = False
    unread_badge: str | None = None
    confidence: float = 0.0
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)


class RecognitionResult(BaseModel):
    captured_at: datetime = Field(default_factory=datetime.now)
    region: Region
    cards: list[CandidateCard] = Field(default_factory=list)
    raw_text_blocks: list[TextBlock] = Field(default_factory=list)

    @property
    def unread_count(self) -> int:
        total = 0
        for card in self.cards:
            if not card.unread:
                continue
            if card.unread_badge and card.unread_badge.isdigit():
                total += int(card.unread_badge)
            else:
                total += 1
        return total

    @property
    def unread_contact_count(self) -> int:
        return sum(1 for card in self.cards if card.unread)

    def summaries(self) -> Sequence[str]:
        return [card.summary for card in self.cards if card.summary]
