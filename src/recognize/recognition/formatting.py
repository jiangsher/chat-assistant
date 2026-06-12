from __future__ import annotations

from recognize.models.recognition_result import CandidateCard, RecognitionResult
from recognize.recognition.card_labels import title_label_for_card
from recognize.recognition.page_signature import PageSignature


def format_unread_card(card: CandidateCard) -> str:
    unread_text = (
        f"[未读 {card.unread_badge}] "
        if card.unread and card.unread_badge
        else "[未读] "
    )
    header_parts = [f"{unread_text}{card.name}".strip()]
    if card.time:
        header_parts.append(card.time)

    lines = ["  ".join(part for part in header_parts if part)]
    if card.title:
        lines.append(f"{title_label_for_card(card)}：{card.title}")
    if card.summary:
        lines.append(f"消息：{card.summary}")
    return "\n".join(lines)


def unread_cards(result: RecognitionResult) -> list[CandidateCard]:
    return [card for card in result.cards if card.unread]


def format_unread_cards_for_copy(result: RecognitionResult) -> str:
    return "\n\n".join(format_unread_card(card) for card in unread_cards(result))


def format_debug_info(
    result: RecognitionResult,
    page_signature: PageSignature | None,
) -> str:
    signature_text = (
        f"{page_signature.template or 'unknown'} / {page_signature.title or '无标题'}"
        if page_signature
        else "unknown"
    )
    raw_preview = "\n".join(
        f"- {block.text} {block.bbox}"
        for block in result.raw_text_blocks[:12]
        if block.text
    )
    return (
        "[调试]\n"
        f"页面：{signature_text}\n"
        f"区域：{result.region.x},{result.region.y} {result.region.width}x{result.region.height}\n"
        f"OCR：{len(result.raw_text_blocks)}  卡片：{len(result.cards)}  "
        f"未读联系人：{result.unread_contact_count}  未读：{result.unread_count}\n"
        f"原始 OCR：\n{raw_preview}"
    )
