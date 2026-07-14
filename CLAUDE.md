# 贸易金融业务管理系统 — 项目说明

## 项目概述

公司贸易金融业务管理系统，覆盖业务计算器、三阶段业务统计（投标/中标/完成）、贸易子公司贷款类业务统计、贸易子公司统计，以及飞书每日 18:00 自动日报推送。

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
- **trade_stats 表**：三阶段统计共用，`stage` 字段区分（`bid`/`win`/`done`）
- **loan_businesses 表**：贷款业务独立表（独立统计、独立通知）
- **subsidiary_companies 表**：贸易子公司信息汇总表（独立统计，仅查看，不推送飞书日报）

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
```

### 飞书推送
- Webhook URL：通过环境变量 `FEISHU_TRADE_WEBHOOK` 读取（GitHub Secrets）
- Supabase Key：通过环境变量 `FEISHU_SUPABASE_KEY` 读取（GitHub Secrets）
- 推送卡片格式：`msg_type: interactive`，蓝色 header template，lark_md 正文

## 主页卡片结构

```
🧮 业务计算器（max-width: 1008px，每行3张）
  └── 银承套利 | 信用证套利 | 报价计算器

📋 贸易业务统计汇总（max-width: 1008px，每行3张）
  └── 📝 投标阶段 | 🏆 中标阶段 | ✅ 完成阶段
  └── 💰 贸易子公司贷款类业务统计（第二行左对齐）
  └── 🏢 贸易子公司统计（第三行左对齐，仅查看，不推送飞书日报）
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
| `region` | 地址（市/区） |
| `paid_capital` | 实缴资本（万元） |
| `long_term_invoice_quota` | 长期发票额度（万元） |
| `social_insurance_count` | 社保人数（整数） |
| `invoice_issued_6m` | 前6月已开发票量（万元） |
| `invoice_used_6m` | 前6月使用发票量（万元） |
| 前6月剩余发票量 | **前端自动计算**：invoice_issued_6m - invoice_used_6m |
