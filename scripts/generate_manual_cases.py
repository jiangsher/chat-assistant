from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QGuiApplication, QImage, QPainter, QPen


WIDTH = 760
HEIGHT = 980
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "test_assets" / "manual_cases"


def load_font_family() -> str:
    app = QGuiApplication.instance() or QGuiApplication([])
    _ = app
    for font_path in (
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    ):
        if not font_path.exists():
            continue
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            return families[0]
    return "Arial"


FONT_FAMILY = load_font_family()


def painter_for() -> tuple[QImage, QPainter]:
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB32)
    image.fill(QColor("#f4f6f8"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    return image, painter


def draw_text(
    painter: QPainter,
    x: int,
    y: int,
    value: str,
    size: int = 16,
    color: str = "#17202a",
    weight: QFont.Weight = QFont.Weight.Normal,
    width: int = 620,
    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
) -> None:
    painter.setPen(QColor(color))
    font = QFont(FONT_FAMILY, size)
    font.setWeight(weight)
    painter.setFont(font)
    painter.drawText(
        QRectF(x, y, width, size * 1.8),
        align | Qt.AlignmentFlag.AlignVCenter,
        value,
    )


def rounded(
    painter: QPainter,
    x: int,
    y: int,
    width: int,
    height: int,
    color: str,
    radius: int = 8,
    border: str | None = None,
) -> None:
    painter.setBrush(QColor(color))
    painter.setPen(QPen(QColor(border), 1) if border else Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(x, y, width, height), radius, radius)


def draw_badge(painter: QPainter, cx: int, cy: int, value: int, color: str = "#ff4d67") -> None:
    label = str(value)
    radius = 13 if len(label) == 1 else 16
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
    draw_text(
        painter,
        cx - radius,
        cy - radius - 1,
        label,
        11,
        "#ffffff",
        QFont.Weight.Bold,
        radius * 2,
        Qt.AlignmentFlag.AlignCenter,
    )


def draw_avatar(painter: QPainter, x: int, y: int, label: str, color: str) -> None:
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(QRectF(x, y, 56, 56))
    draw_text(
        painter,
        x,
        y + 9,
        label[:1],
        18,
        "#ffffff",
        QFont.Weight.Bold,
        56,
        Qt.AlignmentFlag.AlignCenter,
    )


def draw_header(painter: QPainter, title: str, color: str = "#ffffff", fg: str = "#111827") -> None:
    rounded(painter, 0, 0, WIDTH, 72, color, 0)
    draw_text(painter, 28, 18, title, 22, fg, QFont.Weight.Medium, 500)


def draw_card(painter: QPainter, y: int, item: dict[str, object]) -> None:
    rounded(painter, 24, y, WIDTH - 48, 100, str(item.get("bg", "#ffffff")), 8, "#e7ebf0")
    draw_avatar(painter, 48, y + 22, str(item["avatar"]), str(item.get("avatar_color", "#4388d8")))
    if item.get("unread"):
        draw_badge(painter, 98, y + 25, int(item["unread"]))
    draw_text(painter, 126, y + 18, str(item["name"]), 18, "#111827", QFont.Weight.Bold, 360)
    if item.get("meta"):
        draw_text(painter, 286, y + 20, str(item["meta"]), 14, "#4b5563", QFont.Weight.Normal, 300)
    draw_text(painter, WIDTH - 130, y + 20, str(item["time"]), 14, "#8a97a8", width=100)
    draw_text(painter, 126, y + 50, str(item["title"]), 15, str(item.get("title_color", "#2563a8")), width=360)
    draw_text(painter, 126, y + 75, str(item["summary"]), 14, "#667085", width=540)


def save(path: Path, image: QImage, painter: QPainter) -> None:
    painter.end()
    if not image.save(str(path)):
        raise RuntimeError(f"Failed to save {path}")


def render_case(filename: str, title: str, header_color: str, fg: str, cards: list[dict[str, object]]) -> None:
    image, painter = painter_for()
    draw_header(painter, title, header_color, fg)
    y = 88
    for card in cards:
        draw_card(painter, y, card)
        y += 106
    save(OUTPUT_DIR / filename, image, painter)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    render_case(
        "boss_recruiting_8_cards.png",
        "BOSS 候选人消息",
        "#003c3f",
        "#ffffff",
        [
            {"name": "杨莹", "meta": "自拍馆前台日结300-500+包吃住", "title": "女生比较喜欢的那种", "summary": "我下午可以过来面试吗", "time": "14:38", "avatar": "杨", "unread": 3, "avatar_color": "#348bd6"},
            {"name": "吴女士", "meta": "餐饮店员包吃住", "title": "地址在哪", "summary": "附近地铁站方便吗", "time": "14:11", "avatar": "吴", "unread": 1, "avatar_color": "#a86f9b"},
            {"name": "程司鑫宇", "meta": "前台接待 4000-6000", "title": "可以的", "summary": "明天上午十点可以吗", "time": "13:10", "avatar": "程", "unread": 1, "avatar_color": "#ef4f5f"},
            {"name": "谢女士", "meta": "咖啡店服务员", "title": "我看到了", "summary": "需要准备简历吗", "time": "11:06", "avatar": "谢", "unread": 2, "avatar_color": "#f59e0b"},
            {"name": "小穆", "meta": "兼职收银员", "title": "你们还在招人吗", "summary": "我有一年经验", "time": "10:22", "avatar": "穆", "avatar_color": "#15aabf"},
            {"name": "龚万琳", "meta": "行政前台", "title": "有看到过的", "summary": "薪资能面谈吗", "time": "09:18", "avatar": "龚", "unread": 1, "avatar_color": "#7c3aed"},
            {"name": "灵灵", "meta": "自拍馆前台日结300-500+包吃住", "title": "喜欢的[憨笑]", "summary": "我周末有时间", "time": "昨天", "avatar": "灵", "avatar_color": "#4b5563"},
            {"name": "张先生", "meta": "人事助理", "title": "简历已收到", "summary": "稍后给您回复", "time": "周一", "avatar": "张", "avatar_color": "#22c55e"},
        ],
    )

    render_case(
        "gmail_inbox_8_cards.png",
        "Gmail 收件箱",
        "#ffffff",
        "#111827",
        [
            {"name": "alerts@jobs.example", "title": "候选人回复提醒", "summary": "张三回复了你的面试邀请，请及时查看。", "time": "15:02", "avatar": "A", "unread": 4, "avatar_color": "#1a73e8"},
            {"name": "team@example.com", "title": "周报汇总", "summary": "本周招聘数据已更新。", "time": "昨天", "avatar": "T", "avatar_color": "#9aa0a6"},
            {"name": "noreply@crm.example", "title": "新线索分配", "summary": "你有 1 条新的客户咨询待处理。", "time": "周一", "avatar": "N", "unread": 1, "avatar_color": "#1a73e8"},
            {"name": "calendar@example.com", "title": "面试日程变更", "summary": "王女士的面试调整到明天下午三点。", "time": "周一", "avatar": "C", "unread": 2, "avatar_color": "#34a853"},
            {"name": "billing@example.com", "title": "发票申请已提交", "summary": "请在系统中确认开票信息。", "time": "周日", "avatar": "B", "avatar_color": "#fbbc05"},
            {"name": "support@example.com", "title": "客户回复提醒", "summary": "候选人补充了联系方式。", "time": "周六", "avatar": "S", "unread": 1, "avatar_color": "#ea4335"},
            {"name": "hr@company.com", "title": "入职材料提醒", "summary": "请在今天下班前上传身份证照片。", "time": "6月10日", "avatar": "H", "avatar_color": "#673ab7"},
            {"name": "digest@example.com", "title": "每日摘要", "summary": "今日新增 8 条待处理消息。", "time": "6月9日", "avatar": "D", "unread": 3, "avatar_color": "#607d8b"},
        ],
    )

    render_case(
        "wecom_messages_8_cards.png",
        "企业微信 消息",
        "#e9edf2",
        "#111827",
        [
            {"name": "招聘协作群", "title": "候选人已通过初筛，请安排面试。", "summary": "李经理：我已经更新表格。", "time": "今天 09:42", "avatar": "招", "unread": 9, "avatar_color": "#3478f6"},
            {"name": "王经理", "title": "把职位预算发我一下。", "summary": "明天上午要过会。", "time": "昨天", "avatar": "王", "unread": 1, "avatar_color": "#3fa65a"},
            {"name": "行政通知", "title": "明天上午 10 点会议。", "summary": "会议室 A 已预定。", "time": "周二", "avatar": "行", "avatar_color": "#9ca3af"},
            {"name": "前台面试安排", "title": "三位候选人需要确认时间。", "summary": "请优先回复未读消息。", "time": "周一", "avatar": "面", "unread": 2, "avatar_color": "#06b6d4"},
            {"name": "财务小陈", "title": "报销单已退回修改。", "summary": "缺少附件截图。", "time": "周一", "avatar": "财", "avatar_color": "#f59e0b"},
            {"name": "运营日报群", "title": "今日线索已同步。", "summary": "新增 15 条，未联系 4 条。", "time": "周日", "avatar": "运", "unread": 5, "avatar_color": "#8b5cf6"},
            {"name": "客服交接群", "title": "夜班遗留 2 个问题。", "summary": "一个退款，一个账号登录。", "time": "周六", "avatar": "客", "unread": 2, "avatar_color": "#ef4444"},
            {"name": "刘女士", "title": "我下午能过来面试。", "summary": "请发一下地址。", "time": "周五", "avatar": "刘", "avatar_color": "#10b981"},
        ],
    )

    render_case(
        "ticket_center_8_cards.png",
        "客服工单中心",
        "#1f2732",
        "#ffffff",
        [
            {"name": "工单 #A1024", "title": "退款咨询", "summary": "客户询问退款多久到账，请优先回复。", "time": "3分钟前", "avatar": "单", "unread": 12, "avatar_color": "#ff5a45"},
            {"name": "工单 #A1019", "title": "物流异常", "summary": "已联系仓库，等待物流反馈。", "time": "1小时前", "avatar": "单", "avatar_color": "#3f7fbd"},
            {"name": "工单 #A1008", "title": "账号无法登录", "summary": "用户连续提交两次验证码失败。", "time": "昨天", "avatar": "单", "unread": 2, "avatar_color": "#f5a400"},
            {"name": "工单 #A1005", "title": "发票抬头修改", "summary": "企业名称需要重新核对。", "time": "昨天", "avatar": "票", "unread": 1, "avatar_color": "#22c55e"},
            {"name": "工单 #A1001", "title": "售后换货", "summary": "商品外包装破损，客户要求换货。", "time": "周二", "avatar": "售", "avatar_color": "#64748b"},
            {"name": "工单 #A0998", "title": "优惠券失效", "summary": "活动券显示不可用。", "time": "周一", "avatar": "券", "unread": 3, "avatar_color": "#8b5cf6"},
            {"name": "工单 #A0991", "title": "配送地址错误", "summary": "客户要求改到公司地址。", "time": "周日", "avatar": "地", "avatar_color": "#0ea5e9"},
            {"name": "工单 #A0987", "title": "支付失败", "summary": "银行卡扣款但订单未生成。", "time": "周六", "avatar": "付", "unread": 1, "avatar_color": "#ef4444"},
        ],
    )

    render_case(
        "linkedin_messages_8_cards.png",
        "LinkedIn 消息",
        "#0a66c2",
        "#ffffff",
        [
            {"name": "Anna Chen", "title": "Product Designer", "summary": "Thanks for connecting, can we talk tomorrow?", "time": "10:20", "avatar": "A", "unread": 2, "avatar_color": "#0a66c2"},
            {"name": "Michael Lee", "title": "HR Manager", "summary": "I sent the JD to your email.", "time": "Yesterday", "avatar": "M", "avatar_color": "#6b7280"},
            {"name": "Sofia Wang", "title": "Recruiter", "summary": "New opening: AI workflow specialist.", "time": "Mon", "avatar": "S", "unread": 5, "avatar_color": "#f08c3a"},
            {"name": "Jason Miller", "title": "Talent Partner", "summary": "Could you share your latest resume?", "time": "Sun", "avatar": "J", "unread": 1, "avatar_color": "#14b8a6"},
            {"name": "Emily Zhang", "title": "Operations Lead", "summary": "Let us schedule a quick intro call.", "time": "Sat", "avatar": "E", "avatar_color": "#8b5cf6"},
            {"name": "David Kim", "title": "Engineering Manager", "summary": "The role is remote friendly.", "time": "Fri", "avatar": "D", "unread": 3, "avatar_color": "#ef4444"},
            {"name": "Grace Liu", "title": "Founder", "summary": "Your automation demo looks interesting.", "time": "Thu", "avatar": "G", "avatar_color": "#22c55e"},
            {"name": "Robert Xu", "title": "Recruiting Consultant", "summary": "Are you open to contract roles?", "time": "Wed", "avatar": "R", "unread": 1, "avatar_color": "#475569"},
        ],
    )

    for path in sorted(OUTPUT_DIR.glob("*.png")):
        print(path)


if __name__ == "__main__":
    main()
