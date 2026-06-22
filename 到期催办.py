# 到期催办——检测本月到期项目并推送提醒
import requests, datetime, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WEBHOOK = os.environ.get("FEISHU_TRADE_WEBHOOK", "")
SB_URL = os.environ.get("FEISHU_SUPABASE_URL", "https://jpcjwhyotcrhxstzwzid.supabase.co/rest/v1/trade_stats")
SB_KEY = os.environ.get("FEISHU_SUPABASE_KEY", "")
HEADERS = {"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY}

def 查询(stage):
    r = requests.get(f"{SB_URL}?stage=eq.{stage}&order=created_at.desc", headers=HEADERS)
    return r.json() if r.status_code == 200 else []

今天 = datetime.date.today()
本月 = f"{今天.year}/{今天.month:02d}"  # 格式匹配 Supabase 的 "2026/05"
下月 = f"{今天.year}/{(今天.month % 12) + 1:02d}"

def 检查到期(stage, 名称):
    数据 = 查询(stage)
    本月到期 = [r for r in 数据 if r.get("time", "") == 本月]
    下月到期 = [r for r in 数据 if r.get("time", "") == 下月]

    if not 本月到期 and not 下月到期:
        return

    lines = [f"📅 **{名称}** 阶段到期提醒\n"]
    if 本月到期:
        lines.append(f"🔴 本月到期 **{len(本月到期)}** 个：")
        for r in 本月到期[:5]:
            lines.append(f"  • {r.get('company','-')} | {r.get('biz_type','-')} | {r.get('amount','-')}万")
    if 下月到期:
        lines.append(f"🟡 下月到期 **{len(下月到期)}** 个：")
        for r in 下月到期[:5]:
            lines.append(f"  • {r.get('company','-')} | {r.get('biz_type','-')} | {r.get('amount','-')}万")

    卡片 = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": f"⏰ 到期催办 · {本月}"}, "template": "red"},
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}},
                {"tag": "hr"},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"催办助手 · {今天}"}]}
            ]
        }
    }
    r = requests.post(WEBHOOK, json=卡片)
    return r.json()

检查到期("bid", "投标")
检查到期("win", "中标")
print("催办检查完成")
