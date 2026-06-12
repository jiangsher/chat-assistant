from __future__ import annotations

from dataclasses import dataclass

from recognize.models.recognition_result import TextBlock
from recognize.recognition.parser import TIME_OR_DATE_RE, clean_text, detect_app_template


@dataclass(frozen=True)
class PageSignature:
    template: str | None
    title: str


def build_page_signature(text_blocks: list[TextBlock]) -> PageSignature | None:
    template = detect_app_template(text_blocks)
    title = detect_page_title(text_blocks)
    if template is None and not title:
        return None
    return PageSignature(template=template, title=title)


def page_signature_changed(
    previous: PageSignature | None,
    current: PageSignature | None,
) -> bool:
    if previous is None or current is None:
        return False

    if previous.template and current.template and previous.template != current.template:
        return True

    return bool(previous.title and current.title and previous.title != current.title)


def detect_page_title(text_blocks: list[TextBlock]) -> str:
    candidates: list[TextBlock] = []
    for block in text_blocks:
        text = clean_text(block.text)
        if (
            not text
            or len(text) < 4
            or block.bbox[1] > 90
            or TIME_OR_DATE_RE.match(text)
            or "@" in text
        ):
            continue
        candidates.append(block)

    if not candidates:
        return ""

    title = sorted(candidates, key=lambda block: (block.bbox[1], block.bbox[0]))[0]
    return clean_text(title.text)
