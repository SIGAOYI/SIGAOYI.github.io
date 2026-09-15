# Gemini Spark 任务：为自动持仓文追加「Gemini 简评」

本站有两类自动文章，都在正文顶部留了「🔷 Gemini 简评」栏，你的任务是给最新一篇填上简评。

## 触发时机
建议**每天运行一次**（例如 UTC 04:00）。
- ARK 周报：每周六 ~02:30 UTC 发布 → 你当天晚些填。
- 13F 季报：出现在某个周一 ~12:00 UTC（每季一次）→ 你次日填。
每天跑、发现没有待填的就跳过，最省心。

## 第 1 步：找到要处理的文章
在仓库 `_posts/` 里，找**最新一篇**满足“两个标记之间仍是占位符（含‘由 Gemini 自动追加’字样）”的文章，只可能是这两种：
- `*-ark-cathie-wood.markdown`（ARK 周报）
- `*-13f-value-investors.markdown`（13F 季报）
若没有待填的，**结束，不做任何改动**。

## 第 2 步：读对应数据（同目录 ark-data/）
- ARK 周报 → `ark-data/<文章日期>.json`：`funds[*].holdings`（持仓/权重）、`week_trades[fund]`（本周买卖 `{buys:[{ticker,company,shares}],sells:[...]}`）。
- 13F 季报 → `ark-data/13f-<报告季末日>.json`（如 `13f-2026-06-30.json`）：`investors[*].{name,holdings,changes}`。
（也可用公开 URL：`https://axelrod.lawootrip.com/ark-data/<文件名>`。）

## 第 3 步：写简评（120–220 字，简体中文）
- ARK：本周关键买卖、明显的加减仓/主题（AI/基因/太空等）、集中度变化。
- 13F：本季重仓与新建/清仓/显著增减、组合集中度与风格。

## 硬性约束（务必遵守）
- **非投资建议**：只客观陈述“发生了什么/数据显示什么”，不得出现“建议买入/卖出/加仓/减仓/看多/看空”等指令性措辞。
- **原创**：不得复制任何第三方（含 Moomoo、券商研报、新闻）正文；可提及公开事实，但用你自己的话。
- **不编造数字**，只用 JSON 里的数据；简体中文。

## 第 4 步：写回并提交
把该文章中这两个标记**之间**的内容整体替换为你的简评 HTML（**保留标记本身**，其余部分一律不动）：
```
<!-- GEMINI_COMMENT_START -->
<!-- GEMINI_COMMENT_END -->
```
建议格式：
```html
<p>……简评正文……</p>
<p style="color:#888;font-size:12px;">🔷 由 Gemini 自动生成，非投资建议。</p>
```
然后提交并推送：commit message 用 `chore(gemini): 追加 Gemini 简评`，push 到 `master`。

## 幂等
若标记之间已是你之前写的简评（非占位符），说明已处理过，**跳过**该篇，不要重复叠加。
