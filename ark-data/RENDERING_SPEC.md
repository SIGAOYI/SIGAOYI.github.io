# ark-data 渲染约定 (RENDERING SPEC)

本文件约定 `ark-data/<YYYY-MM-DD>.json` 的结构与“下游渲染器”（如 Gemini Spark）应如何据此生成博文。
脚本已直接产出成品文章（`_posts/<发布日>-ark-cathie-wood.markdown`）；本 sidecar 仅供你**可选地**加一段自然语言点评/长文分析。

## 命名
- 每个交易日一份：`ark-data/2026-09-14.json`（`date` = ARK 数据日期，美东）。
- 若要发布你自己渲染的版本，请写到 `_posts/<YYYY-MM-DD>-ark-cathie-wood-commentary.markdown`，
  front-matter 需含 `layout: post`、`title`、`date`、`tags`，日期用**运行日**（避免 Jekyll future 过滤）。

## JSON 结构
```
{
  "date": "2026-09-14",              // ARK 数据日期
  "generated_at": "...ISO...",
  "funds": {
    "ARKK": {
      "name": "ARK 旗舰·颠覆式创新",
      "total_mv": 6400000000.0,
      "holdings": [{"ticker","company","shares","mv","weight"}...]    // 按权重降序
    }, ...
  },
  "today_trades": {                    // 当日真实买卖（ARK 官方披露，经 arkfunds.io）
    "ARKK": {"buys":[{"ticker","company","shares"}...], "sells":[{...}...]}, ...
  }
}
```

## 渲染规则（给下游渲染器）
1. **只做原创分析**：可解读买卖含义、仓位变化、集中度、主题（AI/基因/太空等）。
2. **禁止搬运任何第三方（含 Moomoo）文章正文/图**；可致谢并链接，链接合法、转载正文违法。
3. **非投资建议**：保持客观陈述“发生了什么”，附免责声明；不要“推荐买入/卖出”。
4. 你只写文字点评；价格曲线/买卖点/仓位图已由脚本在正文渲染。你需要的字段：`today_trades`（当日买卖）、`funds[*].holdings`（持仓与权重）。
5. 语言：简体中文；标题含数据日期。
