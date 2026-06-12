from recognize.models.config import Region
from recognize.models.recognition_result import CandidateCard, RecognitionResult, TextBlock
from recognize.recognition.formatting import (
    format_debug_info,
    format_unread_card,
    format_unread_cards_for_copy,
)
from recognize.recognition.page_signature import PageSignature


def test_format_unread_card_uses_dynamic_title_label() -> None:
    card = CandidateCard(
        id="1",
        name="招聘协作群",
        title="候选人已通过初筛，请安排面试。",
        title_label="主题",
        summary="李经理：我已经更新表格。",
        time="今天 09:42",
        unread=True,
        unread_badge="9",
    )

    assert format_unread_card(card) == (
        "[未读 9] 招聘协作群  今天 09:42\n"
        "主题：候选人已通过初筛，请安排面试。\n"
        "消息：李经理：我已经更新表格。"
    )


def test_format_unread_cards_for_copy_only_includes_unread_cards() -> None:
    result = RecognitionResult(
        region=Region(x=1, y=2, width=3, height=4),
        cards=[
            CandidateCard(id="1", name="Anna", title="Product Designer", unread=True, unread_badge="2"),
            CandidateCard(id="2", name="Michael", title="HR Manager", unread=False),
        ],
    )

    output = format_unread_cards_for_copy(result)

    assert "[未读 2] Anna" in output
    assert "Michael" not in output


def test_format_debug_info_includes_signature_and_counts() -> None:
    result = RecognitionResult(
        region=Region(x=10, y=20, width=300, height=400),
        raw_text_blocks=[TextBlock(text="企业微信 消息", bbox=(0, 0, 10, 10))],
        cards=[CandidateCard(id="1", unread=True, unread_badge="3")],
    )

    debug = format_debug_info(
        result,
        PageSignature(template="wecom", title="企业微信 消息"),
    )

    assert "页面：wecom / 企业微信 消息" in debug
    assert "区域：10,20 300x400" in debug
    assert "未读联系人：1  未读：3" in debug
