#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cathie Wood / ARK 每日持仓追踪 -> Jekyll 文章自动发布（可视化增强版）

产出（全部确定性、纯脚本、无 LLM、零 token）：
  1) _posts/<发布日>-ark-cathie-wood.markdown  —— 直接发布的富可视化文章：
       · 每只“当日有买卖”的个股：价格曲线(Yahoo) + 买卖点标注(来自持仓diff) + 当前仓位标注
       · ARKK 旗舰 Top15 权重条形图 + 明细表
       · 各基金当日买卖变化表
  2) ark-data/<数据日>.json  —— 结构化原始数据 sidecar（持仓/变化/价格/交易史），供
       下游渲染器（如 Gemini Spark）可选地生成长文点评；约定见 ark-data/RENDERING_SPEC.md
  3) _scripts/state/  —— 每日快照 + trades_history.json（用于逐日 diff 与买卖点累积）

数据源（免费、无 key）：
  · 持仓：ARK 官方每日全持仓 CSV（assets.ark-funds.com）
  · 价格：Yahoo chart API（query1.finance.yahoo.com）

护栏：数据日期未变 -> NO_NEW_DATA；已有基准且当日零变化 -> NO_CHANGES（不刷空帖）。
合规：仅用公开数据做原创整理；不搬运任何第三方文章正文；Moomoo 仅致谢+链接。

用法：python3 _scripts/ark_daily_post.py [--force]
退出码：0=正常（含跳过）；2=拉不到数据。
"""
import csv, io, os, sys, json, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # -> BLOG/
STATE_DIR = os.path.join(ROOT, "_scripts", "state")
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
SPEC_PATH = os.path.join(SIDECAR_DIR, "RENDERING_SPEC.md")
TRADES_PATH = os.path.join(STATE_DIR, "trades_history.json")

ARK_BASE = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/"
YF = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=6mo&interval=1d"
UA = "Mozilla/5.0 (compatible; ark-daily-post/2.0; +https://axelrod.lawootrip.com)"

FUNDS = {
    "ARKK": ("ARK 旗舰·颠覆式创新", "ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv"),
    "ARKW": ("下一代互联网", "ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv"),
    "ARKG": ("基因革命", "ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv"),
    "ARKQ": ("自动化与机器人", "ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv"),
    "ARKF": ("金融科技创新", "ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv"),
    "ARKX": ("太空探索与创新", "ARK_SPACE_EXPLORATION_&_INNOVATION_ETF_ARKX_HOLDINGS.csv"),
}
ORDER = ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF", "ARKX"]
MAX_PRICE_CHARTS = 8
PRIVATE_TICKERS = {"SPCX"}  # ARK 私有持仓占位符：无公开报价（Yahoo 同名票为无关证券，不可作价格图）


# ---------- fetch ----------
def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8-sig", errors="replace")


def fetch_prices(ticker):
    """Yahoo 日线收盘 -> [{'d':'YYYY-MM-DD','c':float}]，失败返回 []。"""
    yf_t = ticker.strip().upper().replace(".", "-")
    if not yf_t or not yf_t[0].isalpha():
        return []
    try:
        txt = fetch_text(YF.format(t=urllib.parse.quote(yf_t)))
        d = json.loads(txt)
        res = d["chart"]["result"][0]
        ts = res["timestamp"]
        cl = res["indicators"]["quote"][0]["close"]
        out = []
        for t, c in zip(ts, cl):
            if c is None:
                continue
            out.append({"d": datetime.date.fromtimestamp(t).isoformat(), "c": round(float(c), 2)})
        # 剔除延迟退市/错配（如 ARK 的私有占位票 SPCX 被 Yahoo 匹配到已退市 SPAC）：最新价过旧则丢弃
        if out and (datetime.date.today() - datetime.date.fromisoformat(out[-1]["d"])).days > 10:
            print(f"[price-stale] {ticker}: last={out[-1]['d']} -> skip")
            return []
        return out
    except Exception as e:
        print(f"[price-skip] {ticker}: {e}")
        return []


# ---------- parse ----------
def num(s):
    if s is None:
        return None
    s = str(s).strip().strip('"').replace("$", "").replace(",", "").replace("%", "").strip()
    if s == "" or s.lower() in ("n/a", "nan"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_holdings(text):
    rdr = csv.reader(io.StringIO(text))
    header, idx, rows, date_str = None, {}, [], None
    for raw in rdr:
        if not raw or all((c or "").strip() == "" for c in raw):
            continue
        if header is None:
            header = [(c or "").strip().lower() for c in raw]
            for key in ("date", "company", "ticker", "cusip", "shares"):
                for i, hh in enumerate(header):
                    if key in hh:
                        idx[key] = i
                        break
            for i, hh in enumerate(header):
                if "market" in hh and "value" in hh:
                    idx["mv"] = i
                if "weight" in hh:
                    idx["weight"] = i
            continue

        def cell(k):
            i = idx.get(k)
            return raw[i].strip() if (i is not None and i < len(raw)) else ""

        d, comp = cell("date"), cell("company")
        if not d or "/" not in d or not comp:
            continue
        if date_str is None:
            date_str = d
        sh, w = num(cell("shares")), num(cell("weight"))
        if sh is None and w is None:
            continue
        rows.append({"company": comp, "ticker": cell("ticker"), "cusip": cell("cusip"),
                     "shares": sh or 0.0, "mv": num(cell("mv")) or 0.0, "weight": w or 0.0})
    return date_str, rows


def key_of(r):
    return r["ticker"] or r["cusip"] or r["company"]


def diff_fund(cur_rows, prev_rows):
    cur = {key_of(r): r for r in cur_rows}
    prev = {key_of(r): r for r in prev_rows}
    new, exited, inc, dec = [], [], [], []
    for k, r in cur.items():
        if k not in prev:
            new.append(r)
        else:
            d = r["shares"] - prev[k]["shares"]
            if abs(d) < 1:
                continue
            rec = dict(r); rec["dshares"] = d; rec["dpct"] = d / (prev[k]["shares"] or 1) * 100.0
            (inc if d > 0 else dec).append(rec)
    for k, r in prev.items():
        if k not in cur:
            exited.append(r)
    new.sort(key=lambda x: -x["weight"]); exited.sort(key=lambda x: -x["mv"])
    inc.sort(key=lambda x: -x["dpct"]); dec.sort(key=lambda x: x["dpct"])
    return {"new": new, "exited": exited, "inc": inc, "dec": dec}


# ---------- format helpers ----------
def fmt_int(x):
    try:
        return f"{int(round(x)):,}"
    except Exception:
        return str(x)


def fmt_mv(x):
    if x >= 1e9:
        return f"${x/1e9:.2f}B"
    if x >= 1e6:
        return f"${x/1e6:.1f}M"
    return f"${x:,.0f}"


def h(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- render ----------
def top_table(rows, n=15, with_shares=True):
    out = ['<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;">',
           '<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>代码</th>'
           + ('<th style="text-align:right;">股数</th>' if with_shares else '')
           + '<th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>']
    for i, r in enumerate(rows[:n], 1):
        out.append(f'<tr style="border-bottom:1px solid #eee;"><td>{i}</td><td>{h(r["company"])}</td><td>{h(r["ticker"])}</td>'
                   + (f'<td style="text-align:right;">{fmt_int(r["shares"])}</td>' if with_shares else '')
                   + f'<td style="text-align:right;">{fmt_mv(r["mv"])}</td><td style="text-align:right;">{r["weight"]:.2f}%</td></tr>')
    out.append('</tbody></table></div>')
    return "\n".join(out)


def change_table(rows, kind):
    if not rows:
        return "<p><em>无</em></p>"
    if kind in ("new", "exited"):
        cols = '<th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">权重</th>'
        body = "".join(f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["company"])}</td><td>{h(r["ticker"])}</td>'
                       f'<td style="text-align:right;">{fmt_int(r["shares"])}</td><td style="text-align:right;">{r["weight"]:.2f}%</td></tr>'
                       for r in rows[:15])
    else:
        cols = '<th>公司</th><th>代码</th><th style="text-align:right;">股数变化</th><th style="text-align:right;">变化%</th><th style="text-align:right;">现权重</th>'
        body = ""
        for r in rows[:15]:
            sign = "+" if r["dshares"] > 0 else ""
            color = "#c0392b" if r["dshares"] > 0 else "#2e7d32"
            body += (f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["company"])}</td><td>{h(r["ticker"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{fmt_int(r["dshares"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{r["dpct"]:.1f}%</td>'
                     f'<td style="text-align:right;">{r["weight"]:.2f}%</td></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;">'
            f'<thead><tr style="text-align:left;border-bottom:2px solid #ccc;">{cols}</tr></thead><tbody>{body}</tbody></table></div>')


ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'


def bar_chart(rows, n=15):
    data = [{"name": (r["ticker"] or r["company"]), "value": round(r["weight"], 2)} for r in rows[:n]][::-1]
    div = "ark_arkk_bar"
    js = ("(function(){var raw=" + json.dumps(data, ensure_ascii=False) + ";"
          "var names=raw.map(function(d){return d.name;});var vals=raw.map(function(d){return d.value;});"
          "function draw(){var el=document.getElementById('" + div + "');if(!el||!window.echarts)return;"
          "var ch=echarts.init(el);ch.setOption({grid:{left:8,right:56,top:10,bottom:10,containLabel:true},"
          "tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:function(v){return v+'%';}},"
          "xAxis:{type:'value',axisLabel:{formatter:'{value}%'}},yAxis:{type:'category',data:names,axisLabel:{fontSize:12}},"
          "series:[{type:'bar',data:vals,barMaxWidth:22,itemStyle:{color:'#c0392b',borderRadius:[0,4,4,0]},"
          "label:{show:true,position:'right',formatter:'{c}%',fontSize:11}}]});"
          "window.addEventListener('resize',function(){ch.resize();});}"
          "if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);setTimeout(function(){clearInterval(t);},6000);}})();")
    return (f'<div id="{div}" style="width:100%;max-width:860px;margin:18px auto;height:{max(360,34*len(data))}px;"></div>\n'
            f'<script>\n{js}\n</script>')


def nearest_close(pmap, dates_sorted, day):
    """返回 <=day 的最近收盘价（date str, close）。"""
    import bisect
    i = bisect.bisect_right(dates_sorted, day) - 1
    if i < 0:
        return None
    d = dates_sorted[i]
    return d, pmap[d]


def price_chart(ticker, company, prices, trades, cur_shares):
    """价格曲线 + 买卖点(scatter) + 当前仓位标注。trades: [{'date','dshares'}] 已按日聚合。"""
    div = "ark_px_" + ticker.lower().replace("-", "_").replace(".", "_")
    dates = [p["d"] for p in prices]
    closes = [p["c"] for p in prices]
    pmap = {p["d"]: p["c"] for p in prices}
    dsorted = sorted(pmap.keys())
    buys, sells = [], []
    for tr in trades:
        np_ = nearest_close(pmap, dsorted, tr["date"])
        if not np_:
            continue
        dd, cc = np_
        pt = {"value": [dd, cc], "delta": int(tr["dshares"])}
        (buys if tr["dshares"] > 0 else sells).append(pt)
    title = f'{ticker} · {company} — 当前 ARK 持仓 {fmt_int(cur_shares)} 股'
    payload = json.dumps({"dates": dates, "closes": closes, "buys": buys, "sells": sells}, ensure_ascii=False)
    js = ("(function(){var D=" + payload + ";"
          "function mk(arr,color,sym){return {type:'scatter',symbol:sym,symbolSize:function(v,p){var d=Math.abs(p.data.delta||0);return Math.max(9,Math.min(30,Math.log10(d+10)*7));},"
          "itemStyle:{color:color},data:arr.map(function(o){return {value:o.value,delta:o.delta};}),"
          "label:{show:true,position:'top',fontSize:10,formatter:function(p){var d=p.data.delta;return (d>0?'+':'')+d.toLocaleString();}},"
          "tooltip:{trigger:'item',formatter:function(p){var d=p.data.delta;return p.data.value[0]+'<br/>'+(d>0?'买入 +':'卖出 ')+d.toLocaleString()+' 股';}}};}"
          "function draw(){var el=document.getElementById('" + div + "');if(!el||!window.echarts)return;var ch=echarts.init(el);"
          "ch.setOption({grid:{left:8,right:16,top:16,bottom:24,containLabel:true},"
          "tooltip:{trigger:'axis'},xAxis:{type:'category',data:D.dates,axisLabel:{fontSize:10}},"
          "yAxis:{type:'value',scale:true,axisLabel:{formatter:'${value}'}},"
          "series:[{type:'line',data:D.closes,showSymbol:false,smooth:true,lineStyle:{width:2,color:'#3b5b92'},name:'收盘价'},"
          "mk(D.buys,'#c0392b','triangle'),mk(D.sells,'#2e7d32','triangle')]});"
          "window.addEventListener('resize',function(){ch.resize();});}"
          "if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);setTimeout(function(){clearInterval(t);},6000);}})();")
    return (f'<p style="margin:14px 0 2px;font-weight:600;">{h(title)}</p>\n'
            f'<div id="{div}" style="width:100%;max-width:860px;margin:0 auto 20px;height:340px;"></div>\n'
            f'<script>\n{js}\n</script>')


def build_markdown(fresh, diffs, data_date, pub_date, had_prev, price_blocks, no_price):
    dt = datetime.date.fromisoformat(data_date)
    codes = [c for c in ORDER if c in fresh]
    total_mv = sum(sum(r["mv"] for r in fresh[c]["rows"]) for c in codes)
    wd = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][dt.weekday()]

    fm = ["---", "layout:     post",
          f'title:      "Cathie Wood / ARK 每日持仓追踪 ({data_date})"',
          f'subtitle:   "{"·".join(codes)} 价格曲线·买卖点·仓位 全景 · 数据源：ARK 官方每日披露"',
          f"date:       {pub_date}", 'author:     "龟龟"', 'header-img: "/img/home-bg.jpg"',
          "catalog:    true", "tags:", "    - 投资", "    - Cathie Wood", "    - ARK", "    - 持仓追踪", "---", "",
          "> 🤖 **每交易日自动更新**。数据来自 ARK Invest 官方每日全持仓披露（assets.ark-funds.com）与 "
          "Yahoo Finance 价格，均为公开信息；本文为基于公开数据的原创整理，**非投资建议**。选题线索来自 "
          "[Moomoo Whale Watch](https://www.moomoo.com/quote/institution-tracking)（仅作线索与致谢，未使用其文章内容）。",
          "",
          f"**数据日期：{data_date}（{wd}）** ｜ 覆盖基金：{len(codes)} 只 ｜ 合计市值约 {fmt_mv(total_mv)}", ""]

    body = ["## 当日概览", ""]
    for c in codes:
        rows = fresh[c]["rows"]; mv = sum(r["mv"] for r in rows)
        top = max(rows, key=lambda r: r["weight"]) if rows else None
        line = f'- **{c}**（{fresh[c]["name"]}）：{len(rows)} 只持仓，规模约 {fmt_mv(mv)}'
        if top:
            line += f'，第一大重仓 **{top["ticker"] or top["company"]}**（{top["weight"]:.2f}%）'
        if had_prev and c in diffs:
            d = diffs[c]
            line += f'；当日 新建 {len(d["new"])} / 清仓 {len(d["exited"])} / 增持 {len(d["inc"])} / 减持 {len(d["dec"])}'
        body.append(line)
    body.append("")

    # 价格曲线 + 买卖点 + 仓位
    body += ["## 价格曲线 · 买卖点 · 仓位", ""]
    if not had_prev:
        body += ["> 首次运行为**基准**：下方展示重点个股价格曲线与当前 ARK 持仓；"
                 "**买卖点（红买/绿卖）将从下一交易日起自动标注在曲线上。**", ""]
    else:
        body += ["> 曲线为 Yahoo 收盘价；🔺红=买入、🔻绿=卖出（点大小≈交易量），标签为当日净买卖股数；标题为当前 ARK 总持仓。", ""]
    if price_blocks:
        body += [ECHARTS_CDN, ""] + price_blocks
    if no_price:
        body += [f"> 无价格数据（私有/非美股，已跳过作图）：{', '.join(no_price)}", ""]

    # ARKK 明细
    if "ARKK" in fresh:
        rows = sorted(fresh["ARKK"]["rows"], key=lambda r: -r["weight"])
        body += ["## ARKK 旗舰：前 15 大重仓（按权重）", "", bar_chart(rows, 15), "", top_table(rows, 15), ""]

    # 变化明细
    body += ["## 当日买卖变化（对比上一交易日）", ""]
    if not had_prev:
        body += ["> 首次运行，已建立基准快照；增/减/新建/清仓从下一交易日起自动出现。", ""]
    else:
        for c in codes:
            d = diffs.get(c)
            if not d:
                continue
            if not any([d["new"], d["exited"], d["inc"], d["dec"]]):
                body += [f"### {c}", "", "> 当日无变化。", ""]
                continue
            body += [f"### {c}（{fresh[c]['name']}）", "",
                     "**🟥 新建仓**", "", change_table(d["new"], "new"), "",
                     "**🟩 清仓**", "", change_table(d["exited"], "exited"), "",
                     "**加仓**", "", change_table(d["inc"], "inc"), "",
                     "**减仓**", "", change_table(d["dec"], "dec"), ""]

    others = [c for c in codes if c != "ARKK"]
    if others:
        body += ["## 其他 ARK 基金 · 前 8 大重仓", ""]
        for c in others:
            rows = sorted(fresh[c]["rows"], key=lambda r: -r["weight"])
            body += [f"### {c}（{fresh[c]['name']}）", "", top_table(rows, 8), ""]

    body += ["---", "",
             "*本页由脚本依据 ARK 官方公开每日持仓 CSV 与 Yahoo 公开价格自动生成，仅供研究记录，"
             "不构成任何投资建议。持仓与权重每日变动，以 ARK 官方披露为准。*"]
    return "\n".join(fm + body) + "\n"


SPEC_TEXT = """# ark-data 渲染约定 (RENDERING SPEC)

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
      "holdings": [{"ticker","company","shares","mv","weight"}...],   // 按权重降序
      "changes": {                    // 对比上一交易日；首日为空
        "new":   [{"ticker","company","shares","weight"}...],
        "exited":[{...}...],
        "inc":   [{"ticker","company","shares","weight","dshares","dpct"}...],
        "dec":   [{...}...]
      }
    }, ...
  },
  "prices": { "TSLA": [{"d":"YYYY-MM-DD","c": 363.4}, ...], ... },     // Yahoo 收盘
  "trades_history": { "TSLA": [{"date","fund","dshares"}...], ... }   // 累积买卖，用于在价格曲线上标注
}
```

## 渲染规则（给下游渲染器）
1. **只做原创分析**：可解读买卖含义、仓位变化、集中度、主题（AI/基因/太空等）。
2. **禁止搬运任何第三方（含 Moomoo）文章正文/图**；可致谢并链接，链接合法、转载正文违法。
3. **非投资建议**：保持客观陈述“发生了什么”，附免责声明；不要“推荐买入/卖出”。
4. 图表语义：价格曲线用 `prices`；买卖点用 `trades_history`（红买/绿卖，点大小≈|dshares|，标签=净股数）；
   仓位用 `holdings` 中该票的 `shares`/`weight`。
5. 语言：简体中文；标题含数据日期。
"""


def load_trades():
    if os.path.exists(TRADES_PATH):
        try:
            return json.load(open(TRADES_PATH, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def main():
    force = "--force" in sys.argv
    for dpath in (STATE_DIR, POSTS_DIR, SIDECAR_DIR):
        os.makedirs(dpath, exist_ok=True)

    fetched = {}
    for code in ORDER:
        name, fn = FUNDS[code]
        try:
            raw = fetch_text(ARK_BASE + fn)
            d, rows = parse_holdings(raw)
            if d and rows:
                fetched[code] = {"name": name, "date": d, "rows": rows, "raw": raw}
                print(f"[ok]   {code} {d} rows={len(rows)}")
            else:
                print(f"[skip] {code} no valid rows")
        except Exception as e:
            print(f"[skip] {code} {e}")

    if not fetched:
        print("NO_DATA")
        return 2

    def iso(mdY):
        return datetime.datetime.strptime(mdY, "%m/%d/%Y").date()

    maxd = max(iso(v["date"]) for v in fetched.values())
    fresh = {c: v for c, v in fetched.items() if iso(v["date"]) == maxd}
    data_date = maxd.isoformat()
    print(f"[info] newest={data_date} fresh={list(fresh)}")

    last_file = os.path.join(STATE_DIR, "last_date.txt")
    last = open(last_file).read().strip() if os.path.exists(last_file) else None
    if last == data_date and not force:
        print("NO_NEW_DATA")
        return 0

    # diff vs 上一快照
    had_prev, diffs = False, {}
    for c, v in fresh.items():
        sp = os.path.join(STATE_DIR, c + ".csv")
        if os.path.exists(sp):
            _, prev = parse_holdings(open(sp, encoding="utf-8").read())
            if prev:
                diffs[c] = diff_fund(v["rows"], prev)
                had_prev = True

    if had_prev and not force:
        tot = sum(len(d["new"]) + len(d["exited"]) + len(d["inc"]) + len(d["dec"]) for d in diffs.values())
        if tot == 0:
            print("NO_CHANGES")
            return 0

    # 累积交易史（用于价格曲线买卖点）
    trades = load_trades()
    for c, d in diffs.items():
        for r in d["inc"] + d["dec"]:
            trades.setdefault(r["ticker"] or r["company"], []).append(
                {"date": data_date, "fund": c, "dshares": int(r["dshares"])})
        for r in d["new"]:
            trades.setdefault(r["ticker"] or r["company"], []).append(
                {"date": data_date, "fund": c, "dshares": int(r["shares"])})

    # 选择要作价格图的个股：当日有买卖的票；首日则用 ARKK 权重前若干
    traded = {}
    for c, d in diffs.items():
        for r in d["new"]:
            traded[r["ticker"]] = traded.get(r["ticker"], 0) + abs(r["shares"])
        for r in d["inc"] + d["dec"]:
            traded[r["ticker"]] = traded.get(r["ticker"], 0) + abs(r["dshares"])
    def chartable(t):
        return bool(t) and t not in PRIVATE_TICKERS
    if traded:
        chart_tickers = [t for t, _ in sorted(traded.items(), key=lambda kv: -kv[1]) if chartable(t)][:MAX_PRICE_CHARTS]
    else:
        chart_tickers = [r["ticker"] for r in sorted(fresh["ARKK"]["rows"], key=lambda r: -r["weight"])
                         if chartable(r["ticker"])][:MAX_PRICE_CHARTS]

    # 当前总持仓（跨基金合计）
    cur_shares_by_t, company_by_t = {}, {}
    for c, v in fresh.items():
        for r in v["rows"]:
            t = r["ticker"]
            if not t:
                continue
            cur_shares_by_t[t] = cur_shares_by_t.get(t, 0) + r["shares"]
            company_by_t.setdefault(t, r["company"])

    # 私有持仓（如 SpaceX/SPCX）无公开报价，单独提示、不作价格图
    private_present = sorted({r["ticker"] for v in fresh.values() for r in v["rows"]
                             if r["ticker"] in PRIVATE_TICKERS})
    prices, no_price, price_blocks = {}, list(private_present), []
    for t in chart_tickers:
        p = fetch_prices(t)
        if not p:
            no_price.append(t)
            continue
        prices[t] = p
        # 聚合该票每日净买卖
        agg = {}
        for tr in trades.get(t, []):
            agg[tr["date"]] = agg.get(tr["date"], 0) + tr["dshares"]
        tlist = [{"date": k, "dshares": v} for k, v in sorted(agg.items()) if abs(v) >= 1]
        price_blocks.append(price_chart(t, company_by_t.get(t, t), p, tlist, cur_shares_by_t.get(t, 0)))

    pub_date = datetime.date.today().isoformat()
    md = build_markdown(fresh, diffs, data_date, pub_date, had_prev, price_blocks, no_price)
    out_path = os.path.join(POSTS_DIR, f"{pub_date}-ark-cathie-wood.markdown")
    open(out_path, "w", encoding="utf-8").write(md)

    # sidecar JSON（供 Gemini 等下游渲染器）
    sidecar = {
        "date": data_date, "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "funds": {c: {"name": v["name"], "total_mv": sum(r["mv"] for r in v["rows"]),
                      "holdings": sorted(v["rows"], key=lambda r: -r["weight"]),
                      "changes": diffs.get(c, {"new": [], "exited": [], "inc": [], "dec": []})}
                  for c, v in fresh.items()},
        "prices": prices,
        "trades_history": trades,
    }
    open(os.path.join(SIDECAR_DIR, f"{data_date}.json"), "w", encoding="utf-8").write(
        json.dumps(sidecar, ensure_ascii=False, indent=2))
    if not os.path.exists(SPEC_PATH):
        open(SPEC_PATH, "w", encoding="utf-8").write(SPEC_TEXT)

    # 更新 state
    for c, v in fresh.items():
        if v["raw"]:
            open(os.path.join(STATE_DIR, c + ".csv"), "w", encoding="utf-8").write(v["raw"])
    json.dump(trades, open(TRADES_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    open(last_file, "w", encoding="utf-8").write(data_date)

    print("POST:" + os.path.relpath(out_path, ROOT))
    print("SIDECAR:" + os.path.relpath(os.path.join(SIDECAR_DIR, f"{data_date}.json"), ROOT))
    print(f"charts={len(price_blocks)} no_price={no_price}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
