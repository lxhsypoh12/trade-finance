# 贸易金融业务管理系统 — 项目说明

## 项目概述

公司贸易金融业务管理系统，覆盖业务计算器、三阶段业务统计（投标/中标/完成）、贸易子公司贷款类业务统计、贸易子公司统计，以及飞书每日 18:00 自动日报推送。

## 任务分级与模型选择规则

本项目后续接收的指令，先分级再执行；派发子代理（Agent 工具）时按级别用 `model` 参数指定性价比最高的模型：

| 级别 | 特征 | 典型任务 | 模型 |
|------|------|---------|------|
| L1 简单 | 单点改动、无需设计 | 文案/样式微调、文件复制同步、数据查询、git 提交推送 | haiku |
| L2 中等 | 单一功能、局部逻辑改动 | 新增卡片/表格字段、导出功能、飞书推送内容调整 | sonnet |
| L3 复杂 | 多文件联动、数据迁移、架构调整 | 跨模块重构、Supabase 表结构变更、复杂 bug 排查 | opus |

- 级别判断不确定时按 L2 处理；执行中发现比预期复杂，升级到更高模型重做
- 主对话直接处理的小任务（不派子代理）不受此表限制
- 涉及数据删除、表结构变更等不可逆操作前，必须先备份（参照 `E:\AI\数据备份\` 的备份方式）

## 文件结构

| 文件 | 用途 | 备注 |
|------|------|------|
| `贸易金融业务管理系统（Supabase）.html` | **当前主版本**（Supabase 云端存储） | 所有功能开发在此文件进行 |
| `index.html` | GitHub Pages 部署副本 | 必须与 Supabase 版本保持同步，每次修改后需手动复制 |
| `贸易金融业务管理系统.html` | 旧版本（localStorage 本地存储） | 已弃用，不再维护 |
| `贸易金融业务管理系统（飞书共享）.html` | 飞书 Base iframe 嵌入版 | 已弃用，不再维护 |
| `飞书关键词助手.py` | 飞书卡片推送核心逻辑 | 含 Supabase 查询 + 飞书 Webhook 发送 |
| `贸易项目推送.py` | 每日推送入口脚本 | GitHub Actions 定时调用 |
| `.github/workflows/daily_push.yml` | GitHub Actions 定时任务 | UTC 9:30（北京 17:30）触发 |
| `贸易金融业务统计表-prompt.md` | 统计系统原始规格文档 | 参考用 |

## 技术架构

### 前端
- 纯 HTML + CSS + JavaScript **单文件**应用
- 无框架，无构建工具，无 node_modules
- 通过 `display: none/block` + `showView()` 实现视图切换（SPA 风格）

### 数据存储：Supabase
- 项目 URL：`https://jpcjwhyotcrhxstzwzid.supabase.co`
- 匿名 Key（公开安全）：`sb_publishable_hE4GbUYp-NYiD1SYBvw0wg_yUNtV6Bg`
- **trade_stats 表**：三阶段统计共用，`stage` 字段区分（`bid`/`win`/`done`）；done 行含 `profit_included` 布尔列（默认 true）——「计入利润」勾选，取消勾选的行不计入网页三汇总与飞书日报总利润
- **loan_businesses 表**：贷款业务独立表（独立统计、独立通知）
- **subsidiary_companies 表**：贸易子公司信息汇总表（独立统计，仅查看，不推送飞书日报）
- **finance_costs 表**：财务看板成本录入表（`cost_type`：fixed=公司固定成本 / chain=链条费 / reimburse=报销费 / other=其他支出；金额单位**元**）

### REST API 封装（HTML 中）
```js
sbGet(stage)       // GET  ?stage=eq.{stage}&order=created_at.desc
sbInsert(records)  // POST Prefer: return=representation
sbUpdate(id,fields)// PATCH ?id=eq.{id}
sbDelete(ids)      // DELETE ?id=in.({ids})

loanGetAll()       // GET  loan_businesses?order=due_date.asc
loanInsert(records)// POST loan_businesses
loanUpdate(id,fields)// PATCH loan_businesses?id=eq.{id}
loanDelete(id)     // DELETE loan_businesses?id=eq.{id}

subsidiaryGetAll()       // GET  subsidiary_companies?order=company_name.asc
subsidiaryInsert(records)// POST subsidiary_companies
subsidiaryUpdate(id,fields)// PATCH subsidiary_companies?id=eq.{id}
subsidiaryDelete(id)     // DELETE subsidiary_companies?id=eq.{id}

finGetAll()        // GET  finance_costs?order=id.asc
finInsert(records) // POST finance_costs（Prefer: return=representation）
finUpdate(id,fields)// PATCH finance_costs?id=eq.{id}
finDelete(ids)     // DELETE finance_costs?id=in.({ids})（单个 id 或数组）
```

### 飞书推送
- Webhook URL：通过环境变量 `FEISHU_TRADE_WEBHOOK` 读取（GitHub Secrets）
- Supabase Key：通过环境变量 `FEISHU_SUPABASE_KEY` 读取（GitHub Secrets）
- 推送卡片格式：`msg_type: interactive`，蓝色 header template，lark_md 正文
- 完成阶段「实际总利润」只统计 `profit_included ≠ false` 的行（`飞书关键词助手.py` 的 `计入利润()` 谓词，与网页三汇总同口径）；财务看板数据**不**推送日报

## 主页卡片结构

```
🧮 业务计算器（max-width: 1008px，每行3张）
  └── 银承套利 | 信用证套利 | 报价计算器

📋 贸易业务统计汇总（max-width: 1008px，每行3张）
  └── 📝 投标阶段 | 🏆 中标阶段 | ✅ 完成阶段
  └── 💰 贸易子公司贷款类业务统计（第二行左对齐）
  └── 🏢 贸易子公司统计（第三行左对齐，仅查看，不推送飞书日报）
  └── 💹 财务看板（第四行左对齐，有前端密码门，不推送飞书日报）
```

- 卡片容器：`.home-cards`，`justify-content: flex-start`，`max-width: 1008px`
- 新增卡片自动换行并与第一行首张卡片左对齐

## JS 对象结构

### `Stats` 对象（三阶段统计）
- `Stats.render(stage)` — 渲染指定阶段表格
- `Stats.addBid()` — 投标阶段添加记录
- `Stats.batchDelete(stage)` — 批量删除
- `Stats.migrateBidToWin()` — 投标→中标迁移
- `Stats.migrateWinToDone()` — 中标→完成迁移
- `Stats.cellUpdate(stage,id,field,value)` — 单元格 onblur 自动保存

### `LoanStats` 对象（贷款统计）
- `LoanStats.render()` — 渲染贷款表格（含行着色）
- `LoanStats.addRecord()` — 添加新记录并进入编辑模式
- `LoanStats.startEdit(id)` / `saveEdit(id)` / `cancelEdit()` — 编辑模式切换
- `LoanStats.deleteRecord(id)` — 删除单条记录
- `LoanStats.exportPDF()` — 导出 PDF

### `SubsidiaryStats` 对象（贸易子公司统计）
- `SubsidiaryStats.render()` — 渲染子公司信息表格
- `SubsidiaryStats.addRecord()` — 添加新记录并进入编辑模式
- `SubsidiaryStats.startEdit(id)` / `saveEdit(id)` / `cancelEdit()` — 编辑模式切换
- `SubsidiaryStats.deleteRecord(id)` — 删除单条记录
- `SubsidiaryStats.exportPDF()` — 导出 PDF
- **前6月剩余发票量** = 前6月已开发票量 - 前6月使用发票量（自动计算，绿色显示）

### `FinanceStats` 对象（财务看板）
- `FinanceStats.cardClick()` / `pwdOk()` — 卡片密码门（前端密码，会话内免重复询问：sessionStorage `fin_unlocked`）
- `FinanceStats.render()` — 加载数据（done/finance_costs/subsidiary_companies）并渲染三大区块
- `FinanceStats.renderSummary()` — ①利润汇总。**finAggregate 口径**：项目收入=Σ勾选自营行利润合计（effProfit，万元）；成本支出=finance_costs 中 fixed/chain/reimburse ÷10000；其他支出=other ÷10000；合计=收入−成本−其他。列布局按所选年分段：≤2026 为「小计|上一年|当年|1-3季度|10-12月」，≥2027（`FIN_MONTHLY_YEAR`）为「小计|上一年|当年|12个月」
- `FinanceStats.openAddMonth()` / `addMonthCol()` / `removeMonthCol(key)` — ＋加月份列（localStorage `finance_extra_months` 记忆，仅本浏览器有效）
- `FinanceStats.renderRevenue()` — ②项目收入明细（只读同步 done 表勾选自营行，21 列含操作列，✏️去修改 跳完成表）
- `FinanceStats.renderTabs()` / `setTab(t)` / `renderCosts()` — ③成本录入四页签（FIN_TABS：fixed/chain/reimburse/other）
- `FinanceStats.addRecord()` / `startEdit(id)` / `saveEdit(id)` / `cancelEdit()` / `deleteRecord(id)` — 成本行内 CRUD（期间选择器仅 全年/月 两档；历史季度记录编辑回显全年、保存转年粒度）
- `FinanceStats.exportExcel()` / `exportPDF()` — 导出：Excel 单文件三段表（汇总含追加列所见即所得＋收入明细 20 列＋成本明细全页签合并，xlsText 防注入＋BOM）；PDF 打印注入标题「贸易板块利润情况」

## 行着色规则（贷款统计）
- 🟢 `#c6f6d5`（绿色）：距到期日 > 2 个月
- 🟡 `#fefcbf`（黄色）：≤ 2 个月且 > 1 个月
- 🔴 `#fed7d7`（红色）：≤ 1 个月

## 修改后必须执行的操作

1. **同步 index.html**：
   ```bash
   cp "贸易金融业务管理系统（Supabase）.html" index.html
   ```

2. **提交并推送**：
   ```bash
   git add "贸易金融业务管理系统（Supabase）.html" index.html
   git commit -m "描述信息"
   git push origin main
   ```

3. **等待 GitHub Pages 重新部署**（约 1-3 分钟）

## Supabase 建表参考（loan_businesses）

```sql
CREATE TABLE loan_businesses (
  id BIGSERIAL PRIMARY KEY,
  company_name TEXT NOT NULL DEFAULT '',
  bank_name TEXT NOT NULL DEFAULT '',
  region TEXT NOT NULL DEFAULT '',
  amount NUMERIC NOT NULL DEFAULT 0,
  biz_type TEXT NOT NULL DEFAULT '',
  start_date DATE,
  due_date DATE,
  remark TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE loan_businesses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "允许匿名读取" ON loan_businesses FOR SELECT TO anon USING (true);
CREATE POLICY "允许匿名插入" ON loan_businesses FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "允许匿名更新" ON loan_businesses FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "允许匿名删除" ON loan_businesses FOR DELETE TO anon USING (true);
```

## Supabase 建表参考（subsidiary_companies）

```sql
CREATE TABLE subsidiary_companies (
  id BIGSERIAL PRIMARY KEY,
  company_name TEXT NOT NULL DEFAULT '',
  established_date DATE,
  registered_capital NUMERIC NOT NULL DEFAULT 0,
  region TEXT NOT NULL DEFAULT '',
  paid_capital NUMERIC NOT NULL DEFAULT 0,
  long_term_invoice_quota NUMERIC NOT NULL DEFAULT 0,
  social_insurance_count INTEGER NOT NULL DEFAULT 0,
  invoice_issued_6m NUMERIC NOT NULL DEFAULT 0,
  invoice_used_6m NUMERIC NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE subsidiary_companies ENABLE ROW LEVEL SECURITY;
CREATE POLICY "允许匿名读取" ON subsidiary_companies FOR SELECT TO anon USING (true);
CREATE POLICY "允许匿名插入" ON subsidiary_companies FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "允许匿名更新" ON subsidiary_companies FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "允许匿名删除" ON subsidiary_companies FOR DELETE TO anon USING (true);
```

字段说明（单位均为"万元"除特别说明外）：
| 字段 | 含义 |
|------|------|
| `company_name` | 公司名称 |
| `established_date` | 成立时间 |
| `registered_capital` | 注册资本（万元） |
| `paid_capital` | 实缴资本（万元） |
| `region` | 地址（市/区） |
| `social_insurance_count` | 社保人数（整数） |
| `long_term_invoice_quota` | 长期发票额度（万元） |
| `invoice_issued_6m` | 前6月已开发票量（万元） |
| `invoice_used_6m` | 前6月使用发票量（万元） |
| 前6月剩余已开发票量 | **前端自动计算**：invoice_issued_6m - invoice_used_6m |

## Supabase 建表参考（finance_costs）

```sql
CREATE TABLE finance_costs (
  id BIGSERIAL PRIMARY KEY,
  cost_type TEXT NOT NULL DEFAULT 'fixed',   -- fixed=公司固定成本 chain=链条费 reimburse=报销费 other=其他支出
  group_name TEXT NOT NULL DEFAULT '',       -- fixed:公司名称 chain:品种(化肥/橡胶…) reimburse/other:留空
  item_name TEXT NOT NULL DEFAULT '',        -- fixed:房租（含水电）/人力成本/代理记账费/税费/其他 chain:链条费/货转仓储费/城投公司利润留存 reimburse:业务招待费/差旅费/礼品… other:自填明细名
  period TEXT NOT NULL DEFAULT '',           -- 年'2025' / 季度'2026-Q1' / 月'2026-10'
  amount NUMERIC NOT NULL DEFAULT 0,         -- 单位：元
  remark TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE finance_costs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "允许匿名读取" ON finance_costs FOR SELECT TO anon USING (true);
CREATE POLICY "允许匿名插入" ON finance_costs FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "允许匿名更新" ON finance_costs FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "允许匿名删除" ON finance_costs FOR DELETE TO anon USING (true);
```

单位与粒度约定：成本按**元**录入存储，财务看板汇总自动 ÷10000 转万元（2位小数）；收入侧 profit_detail 本身即万元。2026 年 10 月起按月录入（用户 2026-11-19 拍板），历史季度记录（2026-Q1/Q2/Q4）保留照常显示，编辑时只能改成年/月粒度。
