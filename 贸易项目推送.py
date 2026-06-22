# 贸易项目每日推送——每天18:00自动发送飞书卡片
import requests, json, datetime, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ===== 配置 =====
WEBHOOK = os.environ.get("FEISHU_TRADE_WEBHOOK", "")
SB_URL = "https://jpcjwhyotcrhxstzwzid.supabase.co/rest/v1/trade_stats"
SB_KEY = os.environ.get("FEISHU_SUPABASE_KEY", "")
HEADERS = {"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY}

# ===== 抓取数据 =====
def 抓取(stage):
    r = requests.get(f"{SB_URL}?stage=eq.{stage}&order=created_at.desc", headers=HEADERS)
    return r.json() if r.status_code == 200 else []

投标数据 = 抓取("bid")
中标数据 = 抓取("win")
今天 = datetime.date.today()

# ===== 构建卡片内容 =====
def 格式化投标(rows):
    if not rows:
        return "📝 **投标阶段**：暂无项目\n"
    lines = [f"📝 **投标阶段**：{len(rows)} 个项目\n"]
    for r in rows[:8]:
        area = r.get("区域", "-")
        company = r.get("城投公司", "-")
        bank = r.get("金融机构", "-")
        scale = r.get("业务规模", "-")
        btype = r.get("业务类型", "-")
        lines.append(f"• {area} | {company} | {bank} | {scale}万 | {btype}")
    if len(rows) > 8:
        lines.append(f"  ...共{len(rows)}条，详情查看系统")
    return "\n".join(lines)

def 格式化中标(rows):
    if not rows:
        return "🏆 **中标阶段**：暂无项目\n"
    total_profit = sum(float(r.get("预计利润", 0) or 0) for r in rows)
    lines = [f"🏆 **中标阶段**：{len(rows)} 个项目 | 预计总利润 {total_profit:.0f}万\n"]
    for r in rows[:8]:
        area = r.get("区域", "-")
        company = r.get("城投公司", "-")
        trader = r.get("贸易方", "-")
        amount = r.get("中标金额", "-")
        profit = r.get("预计利润", "-")
        lines.append(f"• {area} | {company} | {trader} | 中标{amount}万 | 利润{profit}万")
    if len(rows) > 8:
        lines.append(f"  ...共{len(rows)}条，详情查看系统")
    return "\n".join(lines)

投标内容 = 格式化投标(投标数据)
中标内容 = 格式化中标(中标数据)

# ===== 发送卡片 =====
卡片 = {
    "msg_type": "interactive",
    "card": {
        "header": {
            "title": {"tag": "plain_text", "content": f"贸易项目每日速报 · {今天}"},
            "template": "blue"
        },
        "elements": [
            {"tag": "div", "text": {"tag": "lark_md", "content": 投标内容}},
            {"tag": "hr"},
            {"tag": "div", "text": {"tag": "lark_md", "content": 中标内容}},
            {"tag": "hr"},
            {"tag": "note", "elements": [{"tag": "plain_text", "content": f"自动推送 · {datetime.datetime.now().strftime('%H:%M')} · 数据来源：贸易金融业务管理系统"}]}
        ]
    }
}

r = requests.post(WEBHOOK, json=卡片)
结果 = r.json()
if 结果.get("code") == 0:
    print(f"[{datetime.datetime.now():%H:%M:%S}] Push OK - bid:{len(投标数据)} win:{len(中标数据)}")
else:
    print(f"Push FAILED: {结果}")
