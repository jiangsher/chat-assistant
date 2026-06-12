from __future__ import annotations


MANUAL_CASES: dict[str, dict[str, object]] = {
    "boss_recruiting_8_cards.png": {
        "template": "boss",
        "title_label": "岗位",
        "cards": [
            {"name": "杨莹", "title": "自拍馆前台日结300-500+包吃住", "summary": "女生比较喜欢的那种", "time": "14:38", "unread": "3"},
            {"name": "吴女士", "title": "餐饮店员包吃住", "summary": "地址在哪", "time": "14:11", "unread": "1"},
            {"name": "程司鑫宇", "title": "前台接待4000-6000", "summary": "可以的", "time": "13:10", "unread": "1"},
            {"name": "谢女士", "title": "咖啡店服务员", "summary": "我看到了", "time": "11:06", "unread": "2"},
            {"name": "小穆", "title": "兼职收银员", "summary": "你们还在招人吗", "time": "10:22", "unread": None},
            {"name": "龚万琳", "title": "行政前台", "summary": "有看到过的", "time": "09:18", "unread": "1"},
            {"name": "灵灵", "title": "自拍馆前台日结300-500+包吃住", "summary": "喜欢的[憨笑]", "time": "昨天", "unread": None},
            {"name": "张先生", "title": "人事助理", "summary": "简历已收到", "time": "周一", "unread": None},
        ],
    },
    "gmail_inbox_8_cards.png": {
        "template": "gmail",
        "title_label": "主题",
        "cards": [
            {"name": "alerts@jobs.example", "title": "候选人回复提醒", "summary": "张三回复了你的面试邀请，请及时查看。", "time": "15:02", "unread": "4"},
            {"name": "team@example.com", "title": "周报汇总", "summary": "本周招聘数据已更新。", "time": "昨天", "unread": None},
            {"name": "noreply@crm.example", "title": "新线索分配", "summary": "你有1条新的客户咨询待处理。", "time": "周", "unread": "1"},
            {"name": "calendar@example.com", "title": "面试日程变更", "summary": "王女士的面试调整到明天下午三点。", "time": "周", "unread": "2"},
            {"name": "billing@example.com", "title": "发票申请已提交", "summary": "请在系统中确认开票信息。", "time": "周日", "unread": None},
            {"name": "support@example.com", "title": "客户回复提醒", "summary": "候选人补充了联系方式。", "time": "周六", "unread": "1"},
            {"name": "入职材料提醒", "title": "", "summary": "请在今天下班前上传身份证照片。", "time": "", "unread": None},
            {"name": "digest@example.com", "title": "每日摘要", "summary": "今日新增8条待处理消息。", "time": "6月9日", "unread": "3"},
        ],
    },
    "linkedin_messages_8_cards.png": {
        "template": "linkedin",
        "title_label": "岗位",
        "cards": [
            {"name": "Anna Chen", "title": "Product Designer", "summary": "Thanks for connecting, can we talk tomorrow?", "time": "10:20", "unread": "2"},
            {"name": "Michael Lee", "title": "HR Manager", "summary": "IsenttheJDtoyouremail.", "time": "Yesterday", "unread": None},
            {"name": "Sofia Wang", "title": "Recruiter", "summary": "New opening: Al workflow specialist.", "time": "Mon", "unread": "5"},
            {"name": "JasonMiller", "title": "Talent Partner", "summary": "Could you share your latest resume?", "time": "Sun", "unread": "1"},
            {"name": "Emily Zhang", "title": "Operations Lead", "summary": "Letus schedule a quick intro call", "time": "Sat", "unread": None},
            {"name": "David Kim", "title": "Engineering Manager", "summary": "The role is remote friendly.", "time": "Fri", "unread": "3"},
            {"name": "Grace Liu", "title": "Founder", "summary": "Your automation demo looks interesting.", "time": "Thu", "unread": None},
            {"name": "Robert Xu", "title": "Recruiting Consultant", "summary": "Are you open to contract roles?", "time": "Wed", "unread": "1"},
        ],
    },
    "ticket_center_8_cards.png": {
        "template": "ticket",
        "title_label": "问题",
        "cards": [
            {"name": "工单#A1024", "title": "退款咨询", "summary": "客户询问退款多久到账，请优先回复。", "time": "3分钟前", "unread": "12"},
            {"name": "工单#A1019", "title": "物流异常", "summary": "已联系仓库，等待物流反馈。", "time": "1小时前", "unread": None},
            {"name": "工单#A1008", "title": "账号无法登录", "summary": "用户连续提交两次验证码失败。", "time": "昨天", "unread": "2"},
            {"name": "工单#A1005", "title": "发票抬头修改", "summary": "企业名称需要重新核对。", "time": "昨天", "unread": "1"},
            {"name": "工单#A1001", "title": "售后换货", "summary": "商品外包装破损，客户要求换货。", "time": "周二", "unread": None},
            {"name": "工单#A0998", "title": "优惠券失效", "summary": "活动券显示不可用。", "time": "周一", "unread": "3"},
            {"name": "工单#A0991", "title": "配送地址错误", "summary": "客户要求改到公司地址。", "time": "周日", "unread": None},
            {"name": "工单#A0987", "title": "支付失败", "summary": "银行卡扣款但订单未生成。", "time": "周六", "unread": "1"},
        ],
    },
    "wecom_messages_8_cards.png": {
        "template": "wecom",
        "title_label": "主题",
        "cards": [
            {"name": "招聘协作群", "title": "候选人已通过初筛，请安排面试。", "summary": "李经理：我已经更新表格。", "time": "今天09:42", "unread": "9"},
            {"name": "王经理", "title": "把职位预算发我一下。", "summary": "明天上午要过会。", "time": "昨天", "unread": "1"},
            {"name": "行政通知", "title": "明天上午 10 点会议。", "summary": "会议室A已预定。", "time": "周二", "unread": None},
            {"name": "前台面试安排", "title": "三位候选人需要确认时间。", "summary": "请优先回复未读消息。", "time": "周一", "unread": "2"},
            {"name": "财务小陈", "title": "报销单已退回修改。", "summary": "缺少附件截图。", "time": "周一", "unread": None},
            {"name": "运营日报群", "title": "今日线索已同步。", "summary": "新增15条，未联系4条。", "time": "周日", "unread": "5"},
            {"name": "客服交接群", "title": "夜班遗留2个问题。", "summary": "一个退款，一个账号登录。", "time": "周六", "unread": "2"},
            {"name": "刘女士", "title": "我下午能过来面试。", "summary": "请发一下地址。", "time": "周五", "unread": None},
        ],
    },
}


def unread_total(case: dict[str, object]) -> int:
    cards = case["cards"]
    assert isinstance(cards, list)
    total = 0
    for card in cards:
        assert isinstance(card, dict)
        value = card["unread"]
        if isinstance(value, str) and value.isdigit():
            total += int(value)
    return total


def unread_contact_total(case: dict[str, object]) -> int:
    cards = case["cards"]
    assert isinstance(cards, list)
    return sum(1 for card in cards if isinstance(card, dict) and card["unread"])
