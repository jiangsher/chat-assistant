from __future__ import annotations

from recognize.models.recognition_result import CandidateCard


JOB_TITLE_KEYWORDS = (
    "招聘",
    "岗位",
    "职位",
    "HR",
    "猎头",
    "人事",
    "前台",
    "日结",
    "包吃住",
    "兼职",
    "全职",
    "客服",
    "销售",
    "助理",
    "运营",
    "店员",
    "服务员",
    "经理",
    "司机",
    "文员",
    "主播",
    "行政",
    "设计",
    "开发",
    "产品",
    "designer",
    "recruiter",
    "manager",
    "partner",
    "consultant",
    "engineer",
    "engineering",
    "developer",
    "founder",
    "lead",
    "hr",
    "talent",
    "product",
    "operations",
)

ISSUE_TITLE_KEYWORDS = (
    "退款",
    "咨询",
    "账号",
    "登录",
    "物流",
    "异常",
    "无法",
    "失败",
    "报错",
    "工单",
    "售后",
    "投诉",
)

TOPIC_TITLE_KEYWORDS = (
    "提醒",
    "通知",
    "分配",
    "周报",
    "日报",
    "总结",
    "回复",
    "邀请",
    "协作",
    "会议",
    "初筛",
)


def title_label_for_card(card: CandidateCard) -> str:
    if card.title_label:
        return card.title_label

    text = f"{card.name} {card.title} {card.summary}"
    name = card.name.strip()

    if name.startswith("工单"):
        return "问题"

    if contains_any(text, JOB_TITLE_KEYWORDS):
        return "岗位"

    if "@" in name or contains_any(text, TOPIC_TITLE_KEYWORDS):
        return "主题"

    if contains_any(text, ISSUE_TITLE_KEYWORDS):
        return "问题"

    return "主题"


def contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    folded = text.casefold()
    return any(keyword.casefold() in folded for keyword in keywords)
