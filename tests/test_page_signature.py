from recognize.models.recognition_result import TextBlock
from recognize.recognition.page_signature import (
    PageSignature,
    build_page_signature,
    page_signature_changed,
)


def test_build_page_signature_detects_wecom_title() -> None:
    blocks = [
        TextBlock(text="企业微信 消息", bbox=(20, 12, 180, 44)),
        TextBlock(text="招聘协作群", bbox=(120, 110, 240, 140)),
        TextBlock(text="今天 09:42", bbox=(600, 110, 690, 140)),
    ]

    signature = build_page_signature(blocks)

    assert signature == PageSignature(template="wecom", title="企业微信 消息")


def test_page_signature_changed_when_template_changes() -> None:
    previous = PageSignature(template="wecom", title="企业微信 消息")
    current = PageSignature(template="gmail", title="Gmail 收件箱")

    assert page_signature_changed(previous, current)


def test_page_signature_changed_when_title_changes() -> None:
    previous = PageSignature(template="wecom", title="企业微信 消息")
    current = PageSignature(template="wecom", title="客服工单中心")

    assert page_signature_changed(previous, current)


def test_page_signature_does_not_change_when_current_is_unknown() -> None:
    previous = PageSignature(template="wecom", title="企业微信 消息")

    assert not page_signature_changed(previous, None)
