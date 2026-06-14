from recognize.models.recognition_result import TextBlock
from recognize.recognition.parser import (
    clean_text,
    detect_app_template,
    extract_unread_badge,
    parse_candidate_cards,
)
import numpy as np


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Alice   hello\nworld  ") == "Alice hello world"


def test_parse_candidate_cards() -> None:
    blocks = [
        TextBlock(text="Alice Python Hi there", confidence=0.91, bbox=(0, 0, 100, 40)),
    ]

    cards = parse_candidate_cards(blocks)

    assert len(cards) == 1
    assert cards[0].name == "Alice"
    assert cards[0].title == "Python"
    assert cards[0].summary == "Hi there"


def test_parse_boss_style_timed_cards() -> None:
    image = np.zeros((360, 700, 3), dtype=np.uint8)
    image[190:220, 205:235] = [0, 0, 255]
    blocks = [
        TextBlock(
            text="自拍馆前台日结300-500+包吃住_武汉10..1",
            confidence=0.97,
            bbox=(201, 41, 566, 62),
        ),
        TextBlock(
            text="杨莹自拍馆前台日结300-500+包吃住",
            confidence=0.99,
            bbox=(249, 197, 536, 221),
        ),
        TextBlock(text="14:38", confidence=0.98, bbox=(624, 200, 671, 221)),
        TextBlock(
            text="女生比较喜欢的那种",
            confidence=0.99,
            bbox=(250, 233, 402, 254),
        ),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "3")

    assert len(cards) == 1
    assert cards[0].name == "杨莹"
    assert cards[0].title == "自拍馆前台日结300-500+包吃住"
    assert cards[0].summary == "女生比较喜欢的那种"
    assert cards[0].time == "14:38"
    assert cards[0].unread
    assert cards[0].unread_badge == "3"


def test_parse_split_header_row_merges_name_title_before_time() -> None:
    image = np.zeros((180, 900, 3), dtype=np.uint8)
    image[45:68, 395:418] = [0, 0, 255]
    blocks = [
        TextBlock(text="杨莹", confidence=1.0, bbox=(431, 58, 478, 82)),
        TextBlock(
            text="自拍馆前台日结300-500+包吃住",
            confidence=1.0,
            bbox=(495, 60, 733, 79),
        ),
        TextBlock(text="14:38", confidence=0.99, bbox=(798, 57, 844, 80)),
        TextBlock(text="杨", confidence=1.0, bbox=(364, 71, 387, 94)),
        TextBlock(text="女生比较喜欢的那种", confidence=0.96, bbox=(431, 91, 577, 111)),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "3")

    assert len(cards) == 1
    assert cards[0].name == "杨莹"
    assert cards[0].title == "自拍馆前台日结300-500+包吃住"
    assert cards[0].summary == "女生比较喜欢的那种"
    assert cards[0].time == "14:38"
    assert cards[0].unread
    assert cards[0].unread_badge == "3"


def test_avatar_initial_blocks_do_not_create_duplicate_cards() -> None:
    blocks = [
        TextBlock(text="杨莹", confidence=1.0, bbox=(431, 58, 478, 82)),
        TextBlock(text="自拍馆前台日结300-500+包吃住", confidence=1.0, bbox=(495, 60, 733, 79)),
        TextBlock(text="14:38", confidence=0.99, bbox=(798, 57, 844, 80)),
        TextBlock(text="杨", confidence=1.0, bbox=(364, 71, 387, 94)),
        TextBlock(text="女生比较喜欢的那种", confidence=0.96, bbox=(431, 91, 577, 111)),
        TextBlock(text="吴女士自拍馆前台日结300-500+包吃住", confidence=1.0, bbox=(431, 166, 734, 193)),
        TextBlock(text="14:11", confidence=1.0, bbox=(798, 168, 842, 189)),
        TextBlock(text="吴", confidence=1.0, bbox=(364, 182, 387, 205)),
        TextBlock(text="地址在哪", confidence=1.0, bbox=(431, 201, 500, 221)),
        TextBlock(text="程司鑫宝拍馆前台日结300-500+包吃住", confidence=0.97, bbox=(433, 278, 733, 301)),
        TextBlock(text="13:10", confidence=0.98, bbox=(798, 278, 844, 299)),
        TextBlock(text="程", confidence=1.0, bbox=(363, 291, 388, 314)),
        TextBlock(text="可以的", confidence=1.0, bbox=(431, 311, 484, 332)),
        TextBlock(text="灵灵", confidence=1.0, bbox=(431, 389, 478, 413)),
        TextBlock(text="自拍馆前台日结300-500+包吃住", confidence=1.0, bbox=(497, 389, 732, 409)),
        TextBlock(text="06:47", confidence=1.0, bbox=(798, 388, 844, 409)),
        TextBlock(text="灵", confidence=1.0, bbox=(363, 401, 388, 427)),
        TextBlock(text="喜欢的[憨笑]", confidence=0.99, bbox=(430, 419, 525, 444)),
    ]

    cards = parse_candidate_cards(blocks)

    assert [card.name for card in cards] == ["杨莹", "吴女士", "程司鑫宝拍馆", "灵灵"]
    assert [card.summary for card in cards] == [
        "女生比较喜欢的那种",
        "地址在哪",
        "可以的",
        "喜欢的[憨笑]",
    ]


def test_image_mode_does_not_fallback_to_noise_cards() -> None:
    image = np.zeros((120, 240, 3), dtype=np.uint8)
    blocks = [
        TextBlock(text="Codex移动版", confidence=0.99, bbox=(10, 10, 90, 30)),
        TextBlock(text="项目", confidence=0.99, bbox=(10, 40, 50, 60)),
        TextBlock(text="12小时", confidence=0.99, bbox=(120, 80, 180, 100)),
    ]

    cards = parse_candidate_cards(blocks, image)

    assert cards == []


def test_parse_date_rows_and_assigns_badge_to_matching_card() -> None:
    image = np.zeros((260, 560, 3), dtype=np.uint8)
    image[132:154, 70:92] = [0, 0, 255]
    blocks = [
        TextBlock(text="劳女士南方网络丨HR", confidence=0.96, bbox=(115, 27, 320, 54)),
        TextBlock(text="10:03", confidence=0.98, bbox=(465, 30, 518, 54)),
        TextBlock(text="[送达]没有过", confidence=1.0, bbox=(114, 70, 222, 95)),
        TextBlock(
            text="张先生四川科佰人力资源管理|猎头..．昨天",
            confidence=0.96,
            bbox=(114, 143, 517, 173),
        ),
        TextBlock(
            text="你好，简历推荐需补充信息：1，目前..",
            confidence=1.0,
            bbox=(116, 189, 456, 211),
        ),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "1")

    assert len(cards) == 2
    assert not cards[0].unread
    assert cards[0].name == "劳女士"
    assert cards[0].time == "10:03"
    assert cards[1].unread
    assert cards[1].unread_badge == "1"
    assert cards[1].name == "张先生"
    assert cards[1].time == "昨天"


def test_wecom_template_uses_topic_label_even_with_recruiting_words() -> None:
    blocks = [
        TextBlock(text="企业微信 消息", confidence=0.99, bbox=(20, 10, 180, 42)),
        TextBlock(text="招聘协作群", confidence=0.99, bbox=(125, 110, 255, 140)),
        TextBlock(text="今天 09:42", confidence=0.99, bbox=(610, 112, 700, 140)),
        TextBlock(text="候选人已通过初筛，请安排面试。", confidence=0.99, bbox=(125, 145, 430, 170)),
        TextBlock(text="李经理：我已经更新表格。", confidence=0.99, bbox=(125, 172, 360, 195)),
    ]

    cards = parse_candidate_cards(blocks)

    assert len(cards) == 1
    assert cards[0].name == "招聘协作群"
    assert cards[0].title_label == "主题"
    assert cards[0].title == "候选人已通过初筛，请安排面试。"
    assert cards[0].summary == "李经理：我已经更新表格。"


def test_red_avatar_touching_crop_edge_is_not_unread_badge() -> None:
    image = np.zeros((220, 560, 3), dtype=np.uint8)
    image[120:146, 54:80] = [0, 0, 255]
    blocks = [
        TextBlock(
            text="梁文勇成都煜诚盛宏科技|招聘者昨天",
            confidence=0.99,
            bbox=(114, 143, 429, 173),
        ),
        TextBlock(
            text="[送达]搭建过龙虾，codex；sop工作流...",
            confidence=0.99,
            bbox=(115, 189, 462, 211),
        ),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "1")

    assert len(cards) == 1
    assert cards[0].name == "梁文勇"
    assert not cards[0].unread


def test_merged_red_avatar_with_white_digit_is_unread_badge() -> None:
    image = np.zeros((220, 560, 3), dtype=np.uint8)
    image[120:162, 54:112] = [0, 0, 255]
    image[132:145, 98:103] = [255, 255, 255]
    blocks = [
        TextBlock(
            text="程司鑫宇自拍馆前台日结300-500+包吃住",
            confidence=0.99,
            bbox=(114, 143, 429, 173),
        ),
        TextBlock(text="13:10", confidence=0.99, bbox=(472, 145, 519, 172)),
        TextBlock(text="可以的", confidence=0.99, bbox=(115, 189, 462, 211)),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "1")

    assert len(cards) == 1
    assert cards[0].name == "程司鑫宇"
    assert cards[0].unread
    assert cards[0].unread_badge == "1"


def test_read_receipt_summary_overrides_false_unread_badge() -> None:
    image = np.zeros((220, 560, 3), dtype=np.uint8)
    image[120:162, 54:112] = [0, 0, 255]
    image[132:145, 98:103] = [255, 255, 255]
    blocks = [
        TextBlock(
            text="张先生拓保软件|招聘主管",
            confidence=0.99,
            bbox=(114, 143, 330, 173),
        ),
        TextBlock(text="18:04", confidence=0.99, bbox=(472, 145, 519, 172)),
        TextBlock(
            text="[送达]对这个岗位很感兴趣，本人经验...",
            confidence=0.99,
            bbox=(115, 189, 462, 211),
        ),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "1")

    assert len(cards) == 1
    assert cards[0].name == "张先生"
    assert not cards[0].unread
    assert cards[0].unread_badge is None


def test_malformed_read_receipt_summary_overrides_false_unread_badge() -> None:
    image = np.zeros((220, 560, 3), dtype=np.uint8)
    image[120:162, 54:112] = [0, 0, 255]
    image[132:145, 98:103] = [255, 255, 255]
    blocks = [
        TextBlock(
            text="张先生拓保软件|招聘主管",
            confidence=0.99,
            bbox=(114, 143, 330, 173),
        ),
        TextBlock(text="18:04", confidence=0.99, bbox=(472, 145, 519, 172)),
        TextBlock(
            text="[送达对这个岗位很感兴趣，本人经验...",
            confidence=0.99,
            bbox=(115, 189, 462, 211),
        ),
    ]

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "1")

    assert len(cards) == 1
    assert cards[0].name == "张先生"
    assert not cards[0].unread
    assert cards[0].unread_badge is None


def test_qq_template_uses_right_side_badges_and_ignores_avatar_badge_false_positive() -> None:
    image = np.zeros((620, 420, 3), dtype=np.uint8)
    image[415:455, 36:76] = [0, 0, 255]
    image[258:283, 330:355] = [0, 0, 255]
    blocks = [
        TextBlock(text="QQ游戏中心", confidence=0.99, bbox=(92, 226, 213, 250)),
        TextBlock(text="18:55", confidence=0.99, bbox=(315, 227, 358, 248)),
        TextBlock(text="拳皇98终极之战等你来拳释.", confidence=0.99, bbox=(92, 259, 318, 281)),
        TextBlock(text="22届350", confidence=0.99, bbox=(91, 416, 179, 444)),
        TextBlock(text="16:43", confidence=0.99, bbox=(315, 419, 358, 440)),
        TextBlock(text="汇爹：嘻嘻", confidence=0.99, bbox=(91, 450, 207, 474)),
        TextBlock(text="安徽农业大学互帮..", confidence=0.99, bbox=(91, 505, 279, 531)),
        TextBlock(text="11:13", confidence=0.99, bbox=(315, 506, 357, 527)),
        TextBlock(text="安农第一飞毛腿：可代取..53", confidence=0.99, bbox=(92, 537, 352, 560)),
    ]

    assert detect_app_template(blocks) == "qq"

    cards = parse_candidate_cards(blocks, image, badge_reader=lambda _: "5")
    by_name = {card.name: card for card in cards}

    assert by_name["QQ游戏中心"].unread
    assert by_name["QQ游戏中心"].unread_badge == "5"
    assert not by_name["22届350"].unread
    assert by_name["安徽农业大学互帮.."].unread
    assert by_name["安徽农业大学互帮.."].unread_badge == "53"


def test_extract_unread_badge_accepts_avatar_top_right_dot() -> None:
    image = np.zeros((120, 180, 3), dtype=np.uint8)
    name_bbox = (90, 50, 160, 76)
    image[42:55, 70:83] = [0, 0, 255]

    assert extract_unread_badge(image, name_bbox) == "1"


def test_extract_unread_badge_rejects_red_pixels_inside_avatar() -> None:
    image = np.zeros((120, 180, 3), dtype=np.uint8)
    name_bbox = (90, 50, 160, 76)
    image[62:84, 43:61] = [0, 0, 255]

    assert extract_unread_badge(image, name_bbox) is None
