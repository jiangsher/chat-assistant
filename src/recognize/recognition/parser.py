from __future__ import annotations

import re
from collections.abc import Callable

import cv2
import numpy as np

from recognize.models.recognition_result import CandidateCard, TextBlock


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
DATE_RE = re.compile(r"^(今天|昨天|前天|星期[一二三四五六日天]|周[一二三四五六日天]|\d{1,2}月\d{1,2}日)$")
TIME_OR_DATE_RE = re.compile(
    r"^(\d{1,2}:\d{2}|今天\s*\d{1,2}:\d{2}|昨天\s*\d{1,2}:\d{2}|前天\s*\d{1,2}:\d{2}|昨天|前天|星期[一二三四五六日天]|周[一二三四五六日天]?|\d{1,2}月\d{1,2}日|Yesterday|Today|Mon|Tue|Wed|Thu|Fri|Sat|Sun|\d+\s*分钟前|\d+\s*小时前)$",
    re.IGNORECASE,
)
TRAILING_TIME_RE = re.compile(
    r"[.。．·\s]*(\d{1,2}:\d{2}|今天\s*\d{1,2}:\d{2}|昨天\s*\d{1,2}:\d{2}|前天\s*\d{1,2}:\d{2}|昨天|前天|星期[一二三四五六日天]|周[一二三四五六日天]?|\d{1,2}月\d{1,2}日|Yesterday|Today|Mon|Tue|Wed|Thu|Fri|Sat|Sun|\d+\s*分钟前|\d+\s*小时前)$",
    re.IGNORECASE,
)
JOB_KEYWORDS = (
    "自拍馆",
    "前台",
    "日结",
    "包吃住",
    "招聘",
    "兼职",
    "全职",
    "销售",
    "客服",
    "助理",
    "运营",
    "店员",
    "服务员",
    "经理",
    "司机",
    "文员",
    "主播",
    "人事",
    "行政",
    "设计",
    "开发",
    "产品",
)

TEMPLATE_TITLE_LABELS = {
    "boss": "岗位",
    "linkedin": "岗位",
    "gmail": "主题",
    "wecom": "主题",
    "ticket": "问题",
    "qq": "消息",
}
READ_RECEIPT_RE = re.compile(r"^[\[【]?\s*(送达|已读)\s*[\]】]?", re.IGNORECASE)


def parse_candidate_cards(
    text_blocks: list[TextBlock],
    image: np.ndarray | None = None,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
) -> list[CandidateCard]:
    template = detect_app_template(text_blocks)
    if template == "qq":
        qq_cards = parse_qq_candidate_cards(text_blocks, image, badge_reader)
        if qq_cards:
            return qq_cards

    list_cards = parse_list_candidate_cards(text_blocks, image, badge_reader, template)
    if list_cards:
        return list_cards

    cards = parse_timed_candidate_cards(text_blocks, image, badge_reader, template)
    if cards:
        return cards

    if image is not None:
        return []

    if len(text_blocks) > 5:
        return []

    cards: list[CandidateCard] = []
    for index, block in enumerate(text_blocks):
        text = clean_text(block.text)
        if not text:
            continue

        parts = text.split(" ", 2)
        name = parts[0]
        title = parts[1] if len(parts) > 1 else ""
        summary = parts[2] if len(parts) > 2 else text

        cards.append(
            CandidateCard(
                id=f"card_{index + 1:03d}",
                name=name,
                title=title,
                summary=summary,
                confidence=block.confidence,
                bbox=block.bbox,
            )
        )

    return cards


def parse_list_candidate_cards(
    text_blocks: list[TextBlock],
    image: np.ndarray | None = None,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
    template: str | None = None,
) -> list[CandidateCard]:
    blocks = [block for block in text_blocks if clean_text(block.text)]
    header_candidates: list[tuple[TextBlock, str, str]] = []

    for block in sorted(blocks, key=lambda item: item.bbox[1]):
        text = clean_text(block.text)
        if len(text) < 2 or is_summary_text(text) or TIME_OR_DATE_RE.match(text):
            continue

        header_text, time_text = split_trailing_time(text)
        separate_time = find_time_block_for_header(blocks, block)
        if separate_time:
            time_text = clean_text(separate_time.text)
            block = merge_header_row_blocks(blocks, block, separate_time)
            header_text, embedded_time = split_trailing_time(clean_text(block.text))
            if embedded_time:
                time_text = embedded_time

        if len(header_text) < 3 or block.bbox[0] < 60:
            continue
        if is_duplicate_header_candidate(header_candidates, block, time_text):
            continue
        no_time_badge = None
        if not time_text:
            no_time_badge = extract_unread_badge(image, block.bbox, badge_reader)
            previous_header = header_candidates[-1][0] if header_candidates else None
            close_to_previous = (
                previous_header is not None
                and block.bbox[1] - previous_header.bbox[1] < 60
            )
            if close_to_previous:
                continue
            near_page_title = block.bbox[1] < 80
            if no_time_badge is None and (
                not is_header_without_time(header_text)
                or near_page_title
            ):
                continue

        header_candidates.append((block, header_text, time_text))

    cards: list[CandidateCard] = []
    for index, (header_block, header_text, time_text) in enumerate(header_candidates):
        next_top = (
            header_candidates[index + 1][0].bbox[1]
            if index + 1 < len(header_candidates)
            else header_block.bbox[1] + 140
        )
        header_text, embedded_badge = strip_embedded_unread_badge(header_text)
        name, title = split_name_and_title(header_text, "")
        details = find_detail_blocks(blocks, header_block, next_top)
        if title:
            summary = clean_text(details[0].text) if details else ""
        elif len(details) >= 2:
            title = clean_text(details[0].text)
            summary = clean_text(details[1].text)
        elif details:
            summary = clean_text(details[0].text)
        else:
            summary = ""
        unread_badge = embedded_badge or extract_unread_badge(image, header_block.bbox, badge_reader)
        unread = unread_badge is not None
        if has_read_receipt_marker(summary):
            unread_badge = None
            unread = False
        if not time_text and not unread and not details:
            continue

        cards.append(
            CandidateCard(
                id=f"card_{len(cards) + 1:03d}",
                name=name,
                title=title,
                title_label=title_label_for_template(template),
                summary=summary,
                time=time_text,
                unread=unread,
                unread_badge=unread_badge,
                confidence=header_block.confidence,
                bbox=header_block.bbox,
            )
        )

    return cards


def parse_qq_candidate_cards(
    text_blocks: list[TextBlock],
    image: np.ndarray | None = None,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
) -> list[CandidateCard]:
    _ = image, badge_reader
    blocks = [block for block in text_blocks if clean_text(block.text)]
    time_blocks = sorted(
        [
            block
            for block in blocks
            if TIME_OR_DATE_RE.match(clean_text(block.text))
            and 180 <= block.bbox[0] <= 420
        ],
        key=lambda block: block.bbox[1],
    )
    cards: list[CandidateCard] = []

    for index, time_block in enumerate(time_blocks):
        next_top = (
            time_blocks[index + 1].bbox[1]
            if index + 1 < len(time_blocks)
            else time_block.bbox[1] + 100
        )
        name_block = find_qq_name_block(blocks, time_block)
        if name_block is None:
            continue

        summary_block = find_qq_summary_block(blocks, name_block, next_top)
        summary = clean_text(summary_block.text) if summary_block else ""
        summary, embedded_badge = strip_qq_summary_badge(summary, summary_block)
        side_badge = find_qq_side_badge(blocks, name_block, next_top)
        visual_badge = extract_qq_visual_badge(
            image,
            time_block,
            summary_block,
            badge_reader,
        )
        unread_badge = embedded_badge or side_badge or visual_badge

        cards.append(
            CandidateCard(
                id=f"card_{len(cards) + 1:03d}",
                name=clean_text(name_block.text),
                title="",
                title_label=title_label_for_template("qq"),
                summary=summary,
                time=clean_text(time_block.text),
                unread=unread_badge is not None,
                unread_badge=unread_badge,
                confidence=(name_block.confidence + time_block.confidence) / 2,
                bbox=merge_bboxes([name_block.bbox, time_block.bbox]),
            )
        )

    return cards


def find_qq_name_block(
    blocks: list[TextBlock],
    time_block: TextBlock,
) -> TextBlock | None:
    time_y = center_y(time_block.bbox)
    candidates = [
        block
        for block in blocks
        if block is not time_block
        and 70 <= block.bbox[0] < time_block.bbox[0] - 20
        and abs(center_y(block.bbox) - time_y) <= 18
        and len(clean_text(block.text)) >= 2
        and not TIME_OR_DATE_RE.match(clean_text(block.text))
        and not is_qq_summary_like(clean_text(block.text))
    ]
    if not candidates:
        return None

    return min(candidates, key=lambda block: block.bbox[0])


def find_qq_summary_block(
    blocks: list[TextBlock],
    name_block: TextBlock,
    next_top: int,
) -> TextBlock | None:
    candidates = [
        block
        for block in blocks
        if block is not name_block
        and abs(block.bbox[0] - name_block.bbox[0]) <= 12
        and name_block.bbox[3] <= block.bbox[1] < next_top - 6
        and len(clean_text(block.text)) >= 2
        and not TIME_OR_DATE_RE.match(clean_text(block.text))
    ]
    if not candidates:
        return None

    return min(candidates, key=lambda block: block.bbox[1])


def find_qq_side_badge(
    blocks: list[TextBlock],
    name_block: TextBlock,
    next_top: int,
) -> str | None:
    candidates = [
        clean_text(block.text)
        for block in blocks
        if block.bbox[0] >= 300
        and name_block.bbox[1] <= block.bbox[1] < next_top
        and clean_text(block.text).isdigit()
        and 1 <= int(clean_text(block.text)) <= 999
    ]
    if not candidates:
        return None

    return candidates[-1]


def strip_qq_summary_badge(
    summary: str,
    summary_block: TextBlock | None,
) -> tuple[str, str | None]:
    if summary_block is None:
        return summary, None

    match = re.search(r"(.+?)(\d{1,3})$", summary)
    if not match:
        return summary, None

    badge = match.group(2)
    text_without_badge = match.group(1).rstrip()
    likely_badge_area = summary_block.bbox[2] >= 320
    looks_like_badge_suffix = bool(re.search(r"[.。．…]\s*$", text_without_badge))
    if likely_badge_area and looks_like_badge_suffix:
        return text_without_badge, badge

    return summary, None


def is_qq_summary_like(text: str) -> bool:
    return (
        "：" in text
        or ":" in text
        or text.startswith("[")
        or text.startswith("@")
        or text.startswith("来")
        or text.startswith("我")
    )


def extract_qq_visual_badge(
    image: np.ndarray | None,
    time_block: TextBlock,
    summary_block: TextBlock | None,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
) -> str | None:
    if image is None or image.size == 0:
        return None

    y0 = max(0, time_block.bbox[1] - 4)
    y1_source = summary_block.bbox[3] if summary_block is not None else time_block.bbox[3] + 36
    y1 = min(image.shape[0], y1_source + 4)
    x0 = max(0, time_block.bbox[0] - 8)
    x1 = min(image.shape[1], time_block.bbox[2] + 44)
    if x0 >= x1 or y0 >= y1:
        return None

    crop = image[y0:y1, x0:x1, :3]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    red_mask = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
    red_mask |= cv2.inRange(hsv, np.array([170, 80, 80]), np.array([180, 255, 255]))
    gray_mask = (
        (crop[:, :, 0] >= 145)
        & (crop[:, :, 0] <= 225)
        & (crop[:, :, 1] >= 145)
        & (crop[:, :, 1] <= 225)
        & (crop[:, :, 2] >= 145)
        & (crop[:, :, 2] <= 225)
        & (np.max(crop, axis=2) - np.min(crop, axis=2) <= 18)
    ).astype("uint8") * 255
    mask = red_mask | gray_mask

    components = badge_like_components(mask)
    if not components:
        return None

    x, y, width, height, _ = max(components, key=lambda item: item[4])
    pad = 8
    bx0 = max(0, x - pad)
    by0 = max(0, y - pad)
    bx1 = min(crop.shape[1], x + width + pad)
    by1 = min(crop.shape[0], y + height + pad)
    badge_crop = crop[by0:by1, bx0:bx1]

    if badge_reader is not None:
        badge_text = badge_reader(badge_crop)
        if badge_text and badge_text.isdigit():
            return badge_text

    return classify_badge_digits(badge_crop)


def badge_like_components(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    components: list[tuple[int, int, int, int, int]] = []
    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        fill_ratio = area / max(width * height, 1)
        if (
            12 <= width <= 38
            and 12 <= height <= 32
            and area >= 90
            and fill_ratio >= 0.35
        ):
            components.append((x, y, width, height, area))

    return components


def detect_app_template(text_blocks: list[TextBlock]) -> str | None:
    text = " ".join(clean_text(block.text) for block in text_blocks if clean_text(block.text))
    folded = text.casefold()
    if "linkedin" in folded or any(
        word in folded
        for word in (
            "product designer",
            "engineering manager",
            "talent partner",
            "recruiting consultant",
        )
    ):
        return "linkedin"
    if "gmail" in folded or re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+", text):
        return "gmail"
    if "客服工单" in text or "工单#" in text or "工单 #" in text:
        return "ticket"
    if "企业微信" in text or "协作群" in text or "通知" in text:
        return "wecom"
    if any(
        keyword in text
        for keyword in (
            "QQ游戏中心",
            "我的手机",
            "@全体成员",
            "群聊",
            "QQ群",
        )
    ):
        return "qq"
    if any(
        keyword in text
        for keyword in (
            "自拍馆",
            "前台",
            "日结",
            "包吃住",
            "招聘者",
            "人事经理",
            "人力资源",
            "个人简历",
            "HR",
        )
    ):
        return "boss"
    return None


def title_label_for_template(template: str | None) -> str:
    return TEMPLATE_TITLE_LABELS.get(template or "", "")


def has_read_receipt_marker(text: str) -> bool:
    cleaned = clean_text(text)
    return bool(READ_RECEIPT_RE.match(cleaned))


def strip_embedded_unread_badge(text: str) -> tuple[str, str | None]:
    match = re.match(r"^([1-9]\d{0,2})(工单\s*#?[A-Za-z0-9-].*)$", text)
    if match:
        return match.group(2).strip(), match.group(1)
    return text, None


def merge_header_row_blocks(
    blocks: list[TextBlock],
    header_block: TextBlock,
    time_block: TextBlock,
) -> TextBlock:
    row_y = center_y(header_block.bbox)
    time_left = time_block.bbox[0]
    row_blocks: list[TextBlock] = []
    for block in blocks:
        text = clean_text(block.text)
        if (
            block is time_block
            or len(text) < 2
            or TIME_OR_DATE_RE.match(text)
            or is_summary_text(text)
            or block.bbox[0] < 60
            or block.bbox[2] > time_left - 10
            or abs(center_y(block.bbox) - row_y) > 18
        ):
            continue
        row_blocks.append(block)

    if len(row_blocks) <= 1:
        return header_block

    row_blocks = sorted(row_blocks, key=lambda block: block.bbox[0])
    merged_text = join_inline_header_texts([clean_text(block.text) for block in row_blocks])
    confidence = sum(block.confidence for block in row_blocks) / len(row_blocks)
    return TextBlock(
        text=merged_text,
        confidence=confidence,
        bbox=merge_bboxes([block.bbox for block in row_blocks]),
    )


def join_inline_header_texts(parts: list[str]) -> str:
    text = ""
    for part in parts:
        if not part:
            continue
        if text and should_insert_space(text[-1], part[0]):
            text += " "
        text += part
    return text


def should_insert_space(left: str, right: str) -> bool:
    return left.isascii() and right.isascii() and left.isalnum() and right.isalnum()


def is_duplicate_header_candidate(
    header_candidates: list[tuple[TextBlock, str, str]],
    block: TextBlock,
    time_text: str,
) -> bool:
    for existing_block, _, existing_time in header_candidates:
        same_row = abs(center_y(existing_block.bbox) - center_y(block.bbox)) <= 10
        same_time = bool(time_text and existing_time == time_text)
        same_text_area = abs(existing_block.bbox[0] - block.bbox[0]) <= 5
        if same_row and (same_time or same_text_area):
            return True
    return False


def parse_timed_candidate_cards(
    text_blocks: list[TextBlock],
    image: np.ndarray | None = None,
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
    template: str | None = None,
) -> list[CandidateCard]:
    blocks = [block for block in text_blocks if clean_text(block.text)]
    time_blocks = sorted(
        [block for block in blocks if TIME_OR_DATE_RE.match(clean_text(block.text))],
        key=lambda block: block.bbox[1],
    )
    if not time_blocks:
        return []

    title_hint = extract_title_hint(blocks)
    cards: list[CandidateCard] = []

    for index, time_block in enumerate(time_blocks):
        next_top = (
            time_blocks[index + 1].bbox[1]
            if index + 1 < len(time_blocks)
            else time_block.bbox[1] + 140
        )
        name_block = find_name_block(blocks, time_block)
        if name_block is None:
            continue

        name_text, embedded_badge = strip_embedded_unread_badge(clean_text(name_block.text))
        name, title = split_name_and_title(name_text, title_hint)
        summary = find_summary(blocks, name_block, next_top)
        bbox = merge_bboxes([name_block.bbox, time_block.bbox])
        unread_badge = embedded_badge or extract_unread_badge(image, name_block.bbox, badge_reader)
        unread = unread_badge is not None
        if has_read_receipt_marker(summary):
            unread_badge = None
            unread = False

        cards.append(
            CandidateCard(
                id=f"card_{len(cards) + 1:03d}",
                name=name,
                title=title,
                title_label=title_label_for_template(template),
                summary=summary,
                time=clean_text(time_block.text),
                unread=unread,
                unread_badge=unread_badge,
                confidence=(name_block.confidence + time_block.confidence) / 2,
                bbox=bbox,
            )
        )

    return cards


def find_name_block(
    blocks: list[TextBlock],
    time_block: TextBlock,
) -> TextBlock | None:
    time_y = center_y(time_block.bbox)
    candidates = [
        block
        for block in blocks
        if block is not time_block
        and block.bbox[0] < time_block.bbox[0] - 20
        and block.bbox[0] > 80
        and abs(center_y(block.bbox) - time_y) <= 18
        and len(clean_text(block.text)) >= 3
        and not TIME_OR_DATE_RE.match(clean_text(block.text))
    ]
    if not candidates:
        return None

    return max(candidates, key=lambda block: block.bbox[0])


def find_summary(
    blocks: list[TextBlock],
    name_block: TextBlock,
    next_top: int,
) -> str:
    name_left = name_block.bbox[0]
    candidates = [
        block
        for block in blocks
        if block is not name_block
        and abs(block.bbox[0] - name_left) <= 40
        and block.bbox[1] > name_block.bbox[3]
        and block.bbox[1] < next_top - 8
        and not TIME_OR_DATE_RE.match(clean_text(block.text))
    ]
    if not candidates:
        return ""

    return clean_text(sorted(candidates, key=lambda block: block.bbox[1])[0].text)


def find_detail_blocks(
    blocks: list[TextBlock],
    header_block: TextBlock,
    next_top: int,
) -> list[TextBlock]:
    header_left = header_block.bbox[0]
    candidates = [
        block
        for block in blocks
        if block is not header_block
        and block.bbox[0] >= header_left - 10
        and block.bbox[0] <= header_block.bbox[2] + 90
        and block.bbox[1] >= header_block.bbox[3] - 6
        and block.bbox[1] < next_top - 8
        and not TIME_OR_DATE_RE.match(clean_text(block.text))
        and not is_avatar_or_badge_text(block, header_block)
    ]
    return sorted(candidates, key=lambda block: (block.bbox[1], block.bbox[0]))


def extract_title_hint(blocks: list[TextBlock]) -> str:
    header_candidates = [
        clean_text(block.text)
        for block in blocks
        if block.bbox[1] < 90 and block.bbox[0] > 120 and len(clean_text(block.text)) > 8
    ]
    if not header_candidates:
        return ""

    title = max(header_candidates, key=len)
    title = re.split(r"[_｜|]", title, maxsplit=1)[0]
    return title.rstrip(".0123456789")


def split_name_and_title(text: str, title_hint: str) -> tuple[str, str]:
    email_match = re.match(r"^([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)(.*)$", text)
    if email_match:
        return email_match.group(1).strip(), email_match.group(2).strip()

    if re.fullmatch(r"[\u4e00-\u9fff]{2,4}(经理|主管|总监)?", text):
        return text, ""

    ascii_words = text.split()
    if (
        len(ascii_words) <= 4
        and ascii_words
        and all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", word) for word in ascii_words)
    ):
        return text, ""

    if re.match(r"^工单\s*#?[A-Za-z0-9-]+$", text):
        return text, ""

    ticket_match = re.match(r"^(工单\s*#?[A-Za-z0-9-]+)(.+)$", text)
    if ticket_match:
        return ticket_match.group(1).strip(), ticket_match.group(2).strip()

    if title_hint and title_hint in text:
        name, title = text.split(title_hint, 1)
        return name.strip(), f"{title_hint}{title}".strip()

    honorific_match = re.match(r"^(.{1,8}?(?:先生|女士))(.+)$", text)
    if honorific_match:
        return honorific_match.group(1).strip(), honorific_match.group(2).strip()

    keyword_positions = [
        text.find(keyword)
        for keyword in JOB_KEYWORDS
        if 0 < text.find(keyword) <= 6
    ]
    if keyword_positions:
        split_at = min(keyword_positions)
        return text[:split_at].strip(), text[split_at:].strip()

    parts = text.split(" ", 1)
    if len(parts) == 2:
        return parts[0], parts[1]

    if len(text) > 6 and re.match(r"^[\u4e00-\u9fff]{2,4}", text):
        name_len = 3
        return text[:name_len], text[name_len:]

    return text, title_hint


def split_trailing_time(text: str) -> tuple[str, str]:
    match = TRAILING_TIME_RE.search(text)
    if not match:
        return text, ""

    return text[: match.start()].strip(), match.group(1)


def find_time_block_for_header(
    blocks: list[TextBlock],
    header_block: TextBlock,
) -> TextBlock | None:
    header_y = center_y(header_block.bbox)
    candidates = [
        block
        for block in blocks
        if block is not header_block
        and TIME_OR_DATE_RE.match(clean_text(block.text))
        and block.bbox[0] > header_block.bbox[2] + 20
        and abs(center_y(block.bbox) - header_y) <= 20
    ]
    if not candidates:
        return None

    return min(candidates, key=lambda block: abs(center_y(block.bbox) - header_y))


def is_summary_text(text: str) -> bool:
    return text.startswith("[") or text.startswith("你好") or text.startswith("感谢")


def is_header_without_time(text: str) -> bool:
    return bool(re.fullmatch(r"[\u4e00-\u9fff]{3,8}", text))


def is_avatar_or_badge_text(block: TextBlock, header_block: TextBlock) -> bool:
    text = clean_text(block.text)
    if len(text) > 2:
        return False
    return block.bbox[0] < header_block.bbox[0] - 25


def card_has_red_badge(
    image: np.ndarray | None,
    name_bbox: tuple[int, int, int, int],
) -> bool:
    return extract_unread_badge(image, name_bbox) is not None


def extract_unread_badge(
    image: np.ndarray | None,
    name_bbox: tuple[int, int, int, int],
    badge_reader: Callable[[np.ndarray], str | None] | None = None,
) -> str | None:
    if image is None or image.size == 0:
        return None

    x0 = max(0, name_bbox[0] - 60)
    x1 = max(0, name_bbox[0] - 5)
    y0 = max(0, name_bbox[1] - 22)
    y1 = min(image.shape[0], name_bbox[1] + 34)
    if x0 >= x1 or y0 >= y1:
        return None

    crop = image[y0:y1, x0:x1, :3]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask_1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
    mask_2 = cv2.inRange(hsv, np.array([170, 80, 80]), np.array([180, 255, 255]))
    red_mask = mask_1 | mask_2

    components = red_components(red_mask)
    if not components:
        return None

    component = preferred_separate_badge_component(components)
    if component is None:
        largest_component = max(components, key=lambda item: item[4])
        digit_component = find_digit_like_white_component(crop, largest_component)
        if digit_component is None:
            return None

        x, y, width, height, _ = digit_component
        pad = 12
        bx0 = max(0, x - pad)
        by0 = max(0, y - pad)
        bx1 = min(crop.shape[1], x + width + pad)
        by1 = min(crop.shape[0], y + height + pad)
        badge_crop = crop[by0:by1, bx0:bx1]

        classified = classify_badge_digits(badge_crop)
        if classified:
            return classified

        if badge_reader is not None:
            badge_text = badge_reader(badge_crop)
            if badge_text and badge_text.isdigit():
                return badge_text

        return "1"

    x, y, width, height, _ = component
    pad = 8
    bx0 = max(0, x - pad)
    by0 = max(0, y - pad)
    bx1 = min(crop.shape[1], x + width + pad)
    by1 = min(crop.shape[0], y + height + pad)
    badge_crop = crop[by0:by1, bx0:bx1]

    if badge_reader is not None:
        badge_text = badge_reader(badge_crop)
        if badge_text and badge_text.isdigit():
            return badge_text

    classified = classify_badge_digits(badge_crop)
    if classified:
        return classified

    return "1"


def classify_badge_digits(image: np.ndarray) -> str | None:
    if image.size == 0:
        return None

    white_mask = isolate_badge_digit_mask(image)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(white_mask, 8)
    components: list[tuple[int, int, int, int, int]] = []
    min_x = int(image.shape[1] * 0.45) if image.shape[1] > 40 else 0
    max_y = int(image.shape[0] * 0.7)
    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        if (
            2 <= width <= 18
            and 6 <= height <= 24
            and 6 <= area <= 140
            and x >= min_x
            and y <= max_y
        ):
            components.append((x, y, width, height, area))

    if not components:
        return None

    components = sorted(components, key=lambda item: item[0])
    digits = [classify_single_digit(white_mask, component) for component in components]
    digits = [digit for digit in digits if digit]
    return "".join(digits) if digits else None


def isolate_badge_digit_mask(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    white_mask = (
        (image[:, :, 0] > 170)
        & (image[:, :, 1] > 170)
        & (image[:, :, 2] > 170)
    )
    yy, xx = np.ogrid[:height, :width]
    ellipse = (
        ((xx - width / 2) ** 2) / max((width * 0.42) ** 2, 1)
        + ((yy - height / 2) ** 2) / max((height * 0.42) ** 2, 1)
    ) <= 1
    return (white_mask & ellipse).astype("uint8")


def classify_single_digit(
    mask: np.ndarray,
    component: tuple[int, int, int, int, int],
) -> str | None:
    x, y, width, height, _ = component
    digit = mask[y : y + height, x : x + width] > 0
    if digit.size == 0:
        return None

    if width <= 5 and height >= 8:
        return "1"

    top = digit[: max(1, height // 3), :].sum()
    middle = digit[height // 3 : max(height // 3 + 1, 2 * height // 3), :].sum()
    bottom = digit[max(0, 2 * height // 3) :, :].sum()
    left = digit[:, : max(1, width // 2)].sum()
    right = digit[:, max(1, width // 2) :].sum()
    left_upper = digit[: height // 2, : width // 2].sum()
    right_upper = digit[: height // 2, width // 2 :].sum()
    left_lower = digit[height // 2 :, : width // 2].sum()
    right_lower = digit[height // 2 :, width // 2 :].sum()
    bottom_row = digit[max(0, height - 2) :, :].sum()
    row_max = max(int(row.sum()) for row in digit)

    if row_max >= width - 1 and bottom_row <= max(2, width // 2) and right > left:
        return "4"
    if bottom_row >= width and left_lower > left_upper * 2 and right_upper >= right_lower:
        return "2"
    if right_upper >= left_upper * 2 and right_lower >= left_lower:
        return "3"
    if left_upper > right_upper and right_lower > left_lower:
        return "5"
    if top > 0 and middle > 0 and right_lower >= left_lower:
        return "9"

    return None


def red_components(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    components: list[tuple[int, int, int, int, int]] = []
    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        if area >= 30 and width >= 8 and height >= 8:
            components.append((x, y, width, height, area))

    return components


def preferred_separate_badge_component(
    components: list[tuple[int, int, int, int, int]],
) -> tuple[int, int, int, int, int] | None:
    candidates: list[tuple[int, int, int, int, int]] = []
    for component in components:
        x, y, width, height, _ = component
        touches_crop_edge = x <= 5
        badge_sized = 10 <= width <= 32 and 10 <= height <= 32 and width * height >= 120
        near_avatar_top = y <= 22
        if badge_sized and near_avatar_top and not touches_crop_edge:
            candidates.append(component)

    if not candidates:
        return None

    return max(candidates, key=lambda item: item[4])


def find_digit_like_white_component(
    image: np.ndarray,
    red_component: tuple[int, int, int, int, int] | None = None,
) -> tuple[int, int, int, int, int] | None:
    white_mask = (
        (image[:, :, 0] > 190)
        & (image[:, :, 1] > 190)
        & (image[:, :, 2] > 190)
    ).astype("uint8")
    count, labels, stats, _ = cv2.connectedComponentsWithStats(white_mask, 8)

    candidates: list[tuple[int, int, int, int, int]] = []
    min_x = int(image.shape[1] * 0.45)
    for index in range(1, count):
        x, y, width, height, area = (int(value) for value in stats[index])
        digit_sized = 2 <= width <= 14 and 8 <= height <= 20 and 8 <= area <= 80
        in_badge_area = x >= min_x and 8 <= y <= 45
        if red_component is not None:
            rx, ry, rwidth, rheight, _ = red_component
            center_x = x + width / 2
            center_y_value = y + height / 2
            in_badge_area = (
                center_x >= rx + rwidth * 0.62
                and center_x <= rx + rwidth + 4
                and center_y_value >= ry
                and center_y_value <= ry + rheight * 0.58
            )
        if digit_sized and in_badge_area:
            candidates.append((x, y, width, height, area))

    if not candidates:
        return None

    return max(candidates, key=lambda item: (item[3], item[4]))


def merge_bboxes(
    bboxes: list[tuple[int, int, int, int]],
) -> tuple[int, int, int, int]:
    return (
        min(bbox[0] for bbox in bboxes),
        min(bbox[1] for bbox in bboxes),
        max(bbox[2] for bbox in bboxes),
        max(bbox[3] for bbox in bboxes),
    )


def center_y(bbox: tuple[int, int, int, int]) -> float:
    return (bbox[1] + bbox[3]) / 2
