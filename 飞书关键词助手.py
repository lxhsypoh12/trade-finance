# 飞书关键词助手——输入关键词，自动推送对应信息到飞书群
import requests, json, datetime, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WEBHOOK = os.environ.get("FEISHU_TRADE_WEBHOOK", "")

SB_URL = "https://jpcjwhyotcrhxstzwzid.supabase.co/rest/v1/trade_stats"
SB_KEY = os.environ.get("FEISHU_SUPABASE_KEY", "")
HEADERS = {"apikey": SB_KEY, "Authorization": "Bearer " + SB_KEY}

LOAN_URL = "https://jpcjwhyotcrhxstzwzid.supabase.co/rest/v1/loan_businesses"

def 查询(stage):
    r = requests.get(f"{SB_URL}?stage=eq.{stage}&order=created_at.desc", headers=HEADERS)
    return r.json() if r.status_code == 200 else []

def 发卡片(标题, 摘要, 列表行):
    elements = [
        {"tag": "div", "text": {"tag": "lark_md", "content": 摘要}},
    ]
    if 列表行:
        elements.append({"tag": "hr"})
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(列表行)}})
    elements.append({"tag": "hr"})
    elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": f"关键词助手 · {datetime.datetime.now().strftime('%m-%d %H:%M')}"}]})

    卡片 = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": 标题}, "template": "blue"},
            "elements": elements
        }
    }
    return requests.post(WEBHOOK, json=卡片)

# ===== 关键词路由 =====

def 查投标():
    data = 查询("bid")
    if not data: return 发卡片("投标阶段项目汇总", "目前 **无** 投标阶段项目。", [])
    列表 = []
    for r in data[:10]:
        列表.append(f"• {r.get('region','-')} | {r.get('company','-')} | {r.get('bank','-')} | {r.get('amount','-')}万 | {r.get('biz_type','-')}")
    if len(data) > 10: 列表.append(f"...共{len(data)}条，详情查看系统")
    return 发卡片("投标阶段项目汇总", f"共 **{len(data)}** 个项目", 列表)

def 查中标():
    data = 查询("win")
    if not data: return 发卡片("中标阶段项目汇总", "目前 **无** 中标阶段项目。", [])
    total = sum(float(r.get("est_profit", 0) or 0) for r in data)
    列表 = []
    for r in data[:10]:
        利润 = r.get('est_profit') or '-'
        列表.append(f"• {r.get('region','-')} | {r.get('company','-')} | {r.get('trader','-')} | 中标{r.get('win_amount','-')}万 | 利润{利润}万")
    if len(data) > 10: 列表.append(f"...共{len(data)}条，详情查看系统")
    return 发卡片("中标阶段项目汇总", f"共 **{len(data)}** 个项目 | 预计总利润 **{total:.0f}万**", 列表)

def 查完成():
    data = 查询("done")
    if not data: return 发卡片("完成阶段项目汇总", "目前 **无** 完成阶段项目。", [])
    total = sum((float(r.get("actual_revenue") or 0) - float(r.get("actual_cost") or 0)) for r in data)
    列表 = []
    for r in data[:10]:
        实付 = float(r.get('actual_cost') or 0)
        实收 = float(r.get('actual_revenue') or 0)
        列表.append(f"• {r.get('region','-')} | {r.get('company','-')} | 实付{实付} | 实收{实收} | 利润{实收-实付:.2f}万")
    if len(data) > 10: 列表.append(f"...共{len(data)}条，详情查看系统")
    return 发卡片("完成阶段项目汇总", f"共 **{len(data)}** 个项目 | 实际总利润 **{total:.2f}万**", 列表)

def 查全部():
    bid = 查询("bid"); win = 查询("win"); done = 查询("done")
    win_p = sum(float(r.get("est_profit", 0) or 0) for r in win)
    done_p = sum((float(r.get("actual_revenue") or 0) - float(r.get("actual_cost") or 0)) for r in done)
    列表 = [
        f"📝 投标：**{len(bid)}** 个",
        f"🏆 中标：**{len(win)}** 个 | 预计利润 **{win_p:.0f}万**",
        f"✅ 完成：**{len(done)}** 个 | 实际利润 **{done_p:.2f}万**",
    ]
    return 发卡片("贸易项目总览（三阶段）", "今日项目统计", 列表)

def 查贷款到期():
    """查询2个月内即将到期的贷款业务，推送飞书提醒"""
    today = datetime.date.today()
    two_months_later = today + datetime.timedelta(days=61)  # ~2个月
    try:
        r = requests.get(
            f"{LOAN_URL}?due_date=gte.{today.isoformat()}&due_date=lte.{two_months_later.isoformat()}&order=due_date.asc",
            headers=HEADERS
        )
        data = r.json() if r.status_code == 200 else []
    except Exception:
        data = []

    if not data:
        return 发卡片("💰 贷款到期提醒", "目前 **无** 2个月内到期的贷款。✅", [])

    # 分类：紧急（≤1个月）和关注（≤2个月）
    紧急 = []
    关注 = []
    one_month_later = today + datetime.timedelta(days=31)
    for rec in data:
        due_str = rec.get("due_date", "")
        try:
            due_date = datetime.date.fromisoformat(due_str)
        except (ValueError, TypeError):
            continue
        剩余天数 = (due_date - today).days
        行 = f"• {rec.get('company_name','-')} | {rec.get('bank_name','-')} | {rec.get('biz_type','-')} | {rec.get('amount','-')}万 | 到期：{due_str} | 剩余{剩余天数}天"
        if due_date <= one_month_later:
            紧急.append(行)
        else:
            关注.append(行)

    列表行 = []
    if 紧急:
        列表行.append("**🔴 紧急（≤1个月）：**")
        列表行.extend(紧急)
    if 关注:
        if 列表行: 列表行.append("")
        列表行.append("**🟡 关注（≤2个月）：**")
        列表行.extend(关注)

    return 发卡片("💰 贷款到期提醒（2个月内）", f"共 **{len(data)}** 笔即将到期", 列表行)

关键词路由 = {
    "投标": 查投标,
    "中标": 查中标,
    "完成": 查完成,
    "汇总": 查全部,
    "贷款": 查贷款到期,
}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python 飞书关键词助手.py <关键词>")
        print("可用:", ", ".join(关键词路由.keys()))
        sys.exit(1)
    关键词 = sys.argv[1]
    if 关键词 in 关键词路由:
        关键词路由[关键词]()
        print(f"[OK] {关键词}")
    else:
        print(f"未知: {关键词}，可用: {', '.join(关键词路由.keys())}")
