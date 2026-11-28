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
- **trade_stats 表**：三阶段统计共用，`stage` 字段区分（`bid`/`win`/`done`）；done 行含 `profit_included` 布尔列（默认 true）——「计入利润」勾选，取消勾选的行不计入网页三汇总与飞书日报总利润；2026-11-28 起含重点项目看板 4 列：`key_project`（布尔默认 false，「纳入重点项目看板」勾选）、`progress`（项目进展）、`obstacle`（障碍）、`progress_updated_at`（进展最后更新时间）
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

invGetAll()        // GET  self_invoices?order=id.asc
invInsert(records) // POST self_invoices（Prefer: return=representation）
invUpdate(id,fields)// PATCH self_invoices?id=eq.{id}
invDelete(id)      // DELETE self_invoices?id=eq.{id}
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
  └── 💰 贸易子公司贷款类业务统计 | 🏢 贸易子公司统计（仅查看） | ⚠️ 错误总结日志（第二行）
  └── 📖 业务模式指南 | 🎯 重点项目进度看板（第三行左对齐；看板卡 2026-11-28 新增）

💹 财务板块（max-width: 1008px，每行3张；后续财务类模块新增到此标题下）
  └── 💹 财务看板（有前端密码门，不推送飞书日报）
  └── 🧾 自营发票统计（上传模版自动入库 / 筛选 / 导出Excel，不推送飞书日报）
```

- 卡片容器：`.home-cards`，`justify-content: flex-start`，`max-width: 1008px`
- 新增卡片自动换行并与第一行首张卡片左对齐

## JS 对象结构

### `Stats` 对象（三阶段统计）
- `Stats.render(stage)` — 渲染指定阶段表格
- `Stats.addBid()` — 投标阶段添加记录
- `Stats.batchDelete(stage)` — 批量删除
- `Stats.migrateBidToWin()` — 投标→中标迁移（入库前生成项目名称；`selectQuote` 报价选定路径同样生成）
- `Stats.migrateWinToDone()` — 中标→完成迁移（迁移时自动重生成项目名称随新记录入库）
- `Stats.cellUpdate(stage,id,field,value)` — 单元格 onblur 自动保存（三阶段改 time/biz_type/amount/bank 时重算项目名称并入同一 PATCH；bid/win 名称 span 原地更新不整表刷新，done 维持整表重渲染；布尔分支含 profit_included/key_project）
- 三阶段表尾列「纳入重点项目看板」勾选（class=kp-cb，onchange→cellUpdate(stage,id,'key_project',checked)）；列数/colspan 现状：bid 11 列（报价行与空表 colspan=11）、win 15（空表 15）、done 16（空表 16）
- 三阶段表第一列「项目名称」均系统自动生成、只读（2026-11-27 用户拍板）：`autoProjectName(r)` = 金融机构 + 时间规整6位年月（5位数字补月零、6位原样、其余保留修剪原文）+ 业务类型 +（规模）；规模 ≥10000 万换算 X亿（去尾零，如 4.5亿/1.97亿），否则 X万；金额空/0 不输出括号段。表头灰字「(系统自动生成)」；bid/win 名称 span id=`pname-{stage}-{id}`；Excel 导出三阶段首数据列均为项目名称（xlsText 防注入）。done 存量老记录名称不动；bid/win 存量 48 条空名已于 2026-11-27 一次性补齐（补齐前备份 `E:\AI\数据备份\trade_stats备份_2026-11-27投中补名前.json`）

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

### `InvoiceStats` 对象（自营发票统计）
- `InvoiceStats.render()` — 拉 self_invoices → 筛选 → 排序（period desc、同月 id desc）→ 渲染表格＋合计行（当前筛选之和）＋筛选下拉选项
- `InvoiceStats.onFile(evt)` — 懒加载 SheetJS CDN（仅上传时注入 script，带 SRI sha384）→ `_parseWorkbook(wb)` 按表头文字定位模版 6 标黄列（开票日期→'YYYY-MM'、空发票号/空开票日期行跳过、金额归一 number；一行科目＝一条记录、同票多科目行全保留）→ **行级入库规则**：同发票号+同科目+同价税合计＝DELETE 原行＋INSERT 覆盖（used 保留）；不匹配的原记录保留不动、模版行作新行插入 → alert 新增/覆盖/跳过条数
- `InvoiceStats.addRecord()` / `startEdit(id)` / `saveEdit(id)` / `cancelEdit()` / `deleteRecord(id)` — 行内 CRUD（period 用 month 选择器、amount number、used 勾选）
- `InvoiceStats.toggleUsed(id,checked)` — 「是否使用」勾选即时 PATCH，**按发票号联动**（同 invoice_no 所有行一起勾/取消）；勾选行红 loan-row-red / 未勾选绿 loan-row-green
- `InvoiceStats.setFilter(k,v)` / `clearFilters()` — 筛选：销方/购买方/货物下拉（distinct）、是否使用 是/否/全部、开票年月 from~to 范围（任端留空＝不限）
- `InvoiceStats.exportExcel()` — 当前筛选所见即所得导出（含合计行、是否使用→是/否、xlsText 防注入＋BOM），文件名 `自营发票统计_YYYYMMDD.xls`；不做 PDF

### `KeyProjStats` 对象（重点项目进度看板，2026-11-28 上线）
- 数据源：单次 GET `trade_stats?select=*&key_project=eq.true`（服务端过滤，进入看板每次重拉）；三阶段勾选行自动汇入，跨阶段迁移天然携带勾选与进展（迁移为整行复制，零额外代码）
- `KeyProjStats.render()` — load→响应非数组（字段未加）时 #kp-error 降级提示「请先执行加列 SQL」→ _buildToolbar＋_applyFilters；三区块（bid/win/done）上下排、区内 doneTimeVal 降序；空区块提示 colspan 10/11/15
- 只读列：bid 7 列（项目名称/区域/城投公司/业务类型/业务规模/投标时间/负责人）、win 8 列（+贸易方）、done 12 列（+实际利润/收入合计/支出合计/待回款金额，均万元 toFixed(2)）；**`pendingReceive(r)`** = profit_detail 收入项中 payee[k].verified≠true 的金额合计（没填收款信息=未核对计入），无明细/损坏 JSON 回退 actual_revenue||0
- `KeyProjStats.cellSave(id,field,value)` — 项目进展/障碍 textarea onblur 保存，PATCH 恰三键 {字段值, progress_updated_at, updated_at}；时间格 `kput-{id}` 原地更新（YYYY-MM-DD HH:mm，空值灰色「尚未更新」），不整表重渲
- 筛选：区域/城投公司/业务类型/负责人/贸易方五下拉（`_f` 勾选值集），跨字段 AND、字段内 OR；`kpSearch(field,kw)` 输入关键词→「包含 kw」的选项整体设为勾选集（替换式，之后 toggleOpt 手动增减为叠加式）；**贸易方筛选仅作用 win/done 区块（bid 豁免）**；字段空值行在该筛选生效时被滤除；业务类型选项按 BIZ_TYPES 序、其余中文排序、空值不入选项；按钮摘要「首项 等N项」，任一筛选生效显示「✕ 清空筛选」
- 不推送飞书日报；无 Excel/PDF 导出（例会展示直接用网页）
- 部署记录：2026-11-28 用户已在 Supabase 后台执行加列 SQL（key_project/progress/obstacle/progress_updated_at），加列前全表备份 `E:\AI\数据备份\trade_stats备份_2026-11-28重点看板加列前.json`（86 行）

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

## Supabase 建表参考（self_invoices）

```sql
CREATE TABLE self_invoices (
  id BIGSERIAL PRIMARY KEY,
  invoice_no TEXT NOT NULL DEFAULT '',   -- 数电发票号码
  seller TEXT NOT NULL DEFAULT '',       -- 销方名称
  buyer TEXT NOT NULL DEFAULT '',        -- 购买方名称
  period TEXT NOT NULL DEFAULT '',       -- 开票年月 'YYYY-MM'
  goods TEXT NOT NULL DEFAULT '',        -- 货物或应税劳务名称
  amount NUMERIC NOT NULL DEFAULT 0,     -- 价税合计（元）
  used BOOLEAN NOT NULL DEFAULT false,   -- 是否使用
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE self_invoices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "允许匿名读取" ON self_invoices FOR SELECT TO anon USING (true);
CREATE POLICY "允许匿名插入" ON self_invoices FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "允许匿名更新" ON self_invoices FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY "允许匿名删除" ON self_invoices FOR DELETE TO anon USING (true);
```

发票模版：`财务看板资料\全量发票查询导出结果.xlsx`（首工作表、表头第 1 行、6 个标黄列）；解析按**表头文字**定位列（不依赖列序），扫描全部工作表找含"数电发票号码"表头者。
