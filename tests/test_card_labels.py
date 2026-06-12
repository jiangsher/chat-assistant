from recognize.models.recognition_result import CandidateCard
from recognize.recognition.card_labels import title_label_for_card


def test_email_card_title_is_labeled_as_topic() -> None:
    card = CandidateCard(
        id="1",
        name="alerts@jobs.example",
        title="候选人回复提醒",
        summary="张三回复了你的面试邀请，请及时查看。",
    )

    assert title_label_for_card(card) == "主题"


def test_ticket_card_title_is_labeled_as_issue() -> None:
    card = CandidateCard(
        id="1",
        name="工单 #A1024",
        title="退款咨询",
        summary="客户询问退款多久到账，请优先回复。",
    )

    assert title_label_for_card(card) == "问题"


def test_crm_email_card_keeps_topic_label_even_with_consultation_summary() -> None:
    card = CandidateCard(
        id="1",
        name="noreply@crm.example",
        title="新线索分配",
        summary="你有1条新的客户咨询待处理。",
    )

    assert title_label_for_card(card) == "主题"


def test_recruiting_card_title_is_labeled_as_job() -> None:
    card = CandidateCard(
        id="1",
        name="杨莹",
        title="自拍馆前台日结300-500+包吃住",
        summary="女生比较喜欢的那种",
    )

    assert title_label_for_card(card) == "岗位"


def test_english_professional_title_is_labeled_as_job() -> None:
    cards = [
        CandidateCard(id="1", name="Anna Chen", title="Product Designer"),
        CandidateCard(id="2", name="Sofia Wang", title="Recruiter"),
        CandidateCard(id="3", name="David Kim", title="Engineering Manager"),
        CandidateCard(id="4", name="Jason Miller", title="Talent Partner"),
    ]

    assert [title_label_for_card(card) for card in cards] == ["岗位"] * len(cards)
