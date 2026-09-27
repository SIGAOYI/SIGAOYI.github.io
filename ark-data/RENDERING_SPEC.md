# ark-data 数据说明（RENDERING SPEC）

每周一份 `ark-data/<数据日>.json`（数据日＝持仓对应的收盘日，通常为周五；ARK 于下一交易日披露），供 Gemini 简评与其它下游使用。
文章本身已由脚本渲染完成（`_posts/<数据日>-ark-cathie-wood.markdown`）。

```
{
  "date": "2026-09-25",
  "funds": {
    "ARKK": {
      "name": "颠覆式创新",
      "aum": 6.5e9, "aum_prev": 6.3e9, "daum_pct": 3.1,       // 规模及较上周变化%
      "ret_pct": 2.88, "pnl": 1.8e8,                           // 本周 ETF 涨跌% / 估算盈亏(美元)
      "prev_date": "2026-09-18", "quarter_date": "2026-06-26",
      "top": [{"ticker","label","weight","d_week","d_quarter"}...],   // 权重前 10，d_* 为百分点（null=无数据）
      "week_trades": {"buys":[{"ticker","label","pct","shares"}...], "sells":[...]}  // pct=占基金净值%
    }
  }
}
```
约束：非投资建议；只用给定数据；不搬运任何第三方文章正文。
