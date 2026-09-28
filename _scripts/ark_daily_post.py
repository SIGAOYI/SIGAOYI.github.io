#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cathie Wood / ARK 每周持仓追踪 -> Jekyll 文章（数据截至周五收盘，下周一 ARK 披露后自动发布；Gemini 简评一次成文）

文章结构（全部可视化、不用表格）：
  1) 🔷 Gemini 简评（置顶）
  2) 本周概览：ARKK / ARKW / ARKG / ARKQ 卡片（本周涨跌、估算盈亏、规模及较上周变化、净申赎、持仓数）
  3) 每只基金同一套内容：
       · 持仓权重 Top15，并排显示「较上周」「较上季度」权重增减（三栏对齐柱状图）
       · 本周净买卖（占基金净值 %，绿买红卖）
  4) 文末：每只基金前 5 大持仓的近两年价格曲线 + 该基金买卖点（🟢B 买 / 🔴S 卖）

数据源（免费、无 key）：ARK 官方每日持仓 CSV、arkfunds.io（历史持仓 / 交易）、Yahoo（价格）。
口径：ARK 文件日 D 的持仓＝D 前一交易日收盘；周收盘日 W 的持仓取 W 之后第一份文件，上周/上季同理，
      与 ETF 收盘价涨跌、本周交易（上周收盘后至 W）同一窗口。
去重：同一周收盘日只发一篇（last_date）；--force 强制重生成（例如改版后重排本周文章）。
补做过去某周：--date=YYYY-MM-DD，持仓改取 arkfunds 历史，交易/价格截到该日；不改 state/ 与 last_date。
合规：仅用公开数据做原创整理，非投资建议；Moomoo 仅致谢+链接。

用法：python3 _scripts/ark_daily_post.py [--force] [--date=YYYY-MM-DD]
"""
import csv, io, os, re, sys, json, time, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # -> BLOG/
STATE_DIR = os.path.join(ROOT, "_scripts", "state")
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
SPEC_PATH = os.path.join(SIDECAR_DIR, "RENDERING_SPEC.md")

ARK_BASE = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/"
YF = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?range={r}&interval=1d"
AF_TRADES = "https://arkfunds.io/api/v2/etf/trades?symbol={sym}&date_from={dfrom}"
AF_HOLD = "https://arkfunds.io/api/v2/etf/holdings?symbol={sym}&date_from={dfrom}&date_to={dto}"
UA = "Mozilla/5.0 (compatible; ark-weekly-post/3.0; +https://axelrod.lawootrip.com)"

# 展示的基金（SHOW 的顺序即文章顺序）
FUNDS = {
    "ARKK": ("颠覆式创新", "ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv"),
    "ARKW": ("下一代互联网", "ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv"),
    "ARKG": ("基因革命", "ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv"),
    "ARKQ": ("自动化与机器人", "ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv"),
}
SHOW = ["ARKK", "ARKW", "ARKG", "ARKQ"]
TOP_WEIGHT = 15      # 权重图展示前 N 大
TOP_PRICE = 5        # 每只基金画前 N 大持仓的价格曲线
TOP_TRADES = 12      # 本周净买卖图最多展示 N 只
UP, DOWN, BLUE = "#2e9e5b", "#e23b3b", "#3b5b92"   # 绿涨/买（UP），红跌/卖（DOWN），蓝为中性（权重、价格线）

# 常见持仓中文名（有则用中文，无则用代码/精简英文名）
TICKER_CN = {
    "TSLA": "特斯拉", "NVDA": "英伟达", "GOOG": "谷歌", "GOOGL": "谷歌", "AMZN": "亚马逊", "META": "Meta",
    "AAPL": "苹果", "MSFT": "微软", "NFLX": "奈飞", "AVGO": "博通", "TSM": "台积电", "BABA": "阿里巴巴",
    "PDD": "拼多多", "BIDU": "百度", "AMD": "AMD", "PLTR": "Palantir", "COIN": "Coinbase", "HOOD": "Robinhood",
    "SHOP": "Shopify", "RBLX": "Roblox", "ROKU": "Roku", "CRCL": "Circle", "SPCX": "SpaceX", "TEM": "Tempus AI",
    "CRSP": "CRISPR", "TXG": "10x Genomics", "BEAM": "Beam", "NTLA": "Intellia", "TWST": "Twist",
    "CRWV": "CoreWeave", "ABNB": "Airbnb", "DKNG": "DraftKings", "CRWD": "CrowdStrike", "ARKB": "ARK比特币ETF",
    "ACHR": "Archer", "RKLB": "Rocket Lab", "IONS": "Ionis", "ISRG": "直觉外科", "ILMN": "Illumina",
    "TER": "泰瑞达", "DE": "迪尔", "SOFI": "SoFi", "TOST": "Toast", "PATH": "UiPath", "RXRX": "Recursion",
}
COMPANY_CN = {"OPENAI": "OpenAI", "SPACE EXPLORATION": "SpaceX", "ANTHROPIC": "Anthropic", "XAI": "xAI"}


# ---------------- fetch ----------------
def fetch_text(url, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8-sig", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1.5)
    raise last


def fetch_json(url):
    return json.loads(fetch_text(url))


def fetch_prices(ticker, rng="2y"):
    """Yahoo 日线收盘 -> [{'d','c'}]（升序），失败/过旧返回 []。"""
    t = (ticker or "").strip().upper().replace(".", "-")
    if not t or not t[0].isalpha():
        return []
    try:
        d = fetch_json(YF.format(t=urllib.parse.quote(t), r=rng))
        res = d["chart"]["result"][0]
        out = [{"d": datetime.date.fromtimestamp(ts).isoformat(), "c": round(float(c), 2)}
               for ts, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]) if c is not None]
        if out and (datetime.date.today() - datetime.date.fromisoformat(out[-1]["d"])).days > 10:
            print(f"[price-stale] {ticker}")
            return []
        return out
    except Exception as e:
        print(f"[price-skip] {ticker}: {e}")
        return []


def norm_cusip(c):
    c = (c or "").strip().upper()
    return c[2:11] if (len(c) == 12 and c[:2].isalpha()) else c[:9]   # ISIN -> CUSIP


def hkey(ticker, cusip, company=""):
    return (ticker or "").strip().upper() or norm_cusip(cusip) or (company or "").upper()


# ARK 披露口径：文件日期 D 的持仓＝D 前一交易日收盘后的持仓与价格（2026-09 用股价与成交逐只核对过）。
# 所以“某日收盘”的持仓要看它之后的第一份文件；周五收盘要等下周一的文件。
def trading_days():
    """ARKK 日线日期当交易日历（升序）；取不到就退回工作日。"""
    td = [p["d"] for p in fetch_prices("ARKK", "1y")]
    if td:
        return td
    today = datetime.date.today()
    return [d.isoformat() for d in (today - datetime.timedelta(days=i) for i in range(400, -1, -1)) if d.weekday() < 5]


def prev_td(td, day):
    """严格早于 day 的最近交易日。"""
    import bisect
    i = bisect.bisect_left(td, day) - 1
    return td[i] if i >= 0 else None


def last_td(td, day):
    """day 当天或之前的最近交易日。"""
    import bisect
    i = bisect.bisect_right(td, day) - 1
    return td[i] if i >= 0 else None


def prev_week_close(td, day):
    """day 所在周之前那一周的最后一个交易日（通常为上周五）。"""
    d = datetime.date.fromisoformat(day)
    return prev_td(td, (d - datetime.timedelta(days=d.weekday())).isoformat())


def fetch_snapshot_rows(fund, close_date):
    """arkfunds：close_date 收盘时的全部持仓行（与 parse_holdings 同形）-> (文件日期, rows)，取其后第一份披露。"""
    c = datetime.date.fromisoformat(close_date)
    rows = fetch_json(AF_HOLD.format(sym=fund, dfrom=(c + datetime.timedelta(days=1)).isoformat(),
                                     dto=(c + datetime.timedelta(days=8)).isoformat())).get("holdings", [])
    if not rows:
        return None, []
    d = min(x["date"] for x in rows)
    return d, [{"company": x.get("company") or "", "ticker": (x.get("ticker") or "").strip(),
                "cusip": x.get("cusip") or "", "shares": float(x.get("shares") or 0),
                "mv": float(x.get("market_value") or 0), "weight": float(x.get("weight") or 0)}
               for x in rows if x.get("date") == d]


def fetch_snapshot(fund, close_date):
    """同上，返回 (文件日期, {key: {...}})；失败 (None, {})。"""
    try:
        d, rows = fetch_snapshot_rows(fund, close_date)
    except Exception as e:
        print(f"[snap-skip] {fund} {close_date}: {e}")
        return None, {}
    return d, {hkey(r["ticker"], r["cusip"], r["company"]): {"weight": r["weight"], "shares": r["shares"],
                                                             "mv": r["mv"], "company": r["company"]} for r in rows}


def fetch_trades(fund, dfrom):
    """arkfunds 交易 -> [{date,ticker,company,dshares(带符号),pct(占基金%，带符号)}]；失败 None。"""
    try:
        rows = fetch_json(AF_TRADES.format(sym=fund, dfrom=dfrom)).get("trades", [])
    except Exception as e:
        print(f"[trades-skip] {fund}: {e}")
        return None
    out = []
    for x in rows:
        tk = (x.get("ticker") or "").strip()
        sh = int(x.get("shares") or 0)
        if not tk or sh == 0:
            continue
        buy = str(x.get("direction", "")).lower().startswith("b")
        pct = float(x.get("etf_percent") or 0)
        out.append({"date": x["date"], "ticker": tk, "company": x.get("company") or tk,
                    "dshares": sh if buy else -sh, "pct": pct if buy else -pct})
    return out


# ---------------- parse ----------------
def num(s):
    s = str(s or "").strip().strip('"').replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(s) if s and s.lower() not in ("n/a", "nan") else None
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
        date_str = date_str or d
        sh, w = num(cell("shares")), num(cell("weight"))
        if sh is None and w is None:
            continue
        rows.append({"company": comp, "ticker": cell("ticker"), "cusip": cell("cusip"),
                     "shares": sh or 0.0, "mv": num(cell("mv")) or 0.0, "weight": w or 0.0})
    return date_str, rows


# ---------------- format ----------------
def h(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_int(x):
    try:
        return f"{int(round(x)):,}"
    except Exception:
        return str(x)


def money(x, sign=False):
    s = ("+" if x > 0 else "-" if x < 0 else "") if sign else ("-" if x < 0 else "")
    a = abs(x)
    if a >= 1e9:
        return f"{s}${a/1e9:.2f}B"
    if a >= 1e6:
        return f"{s}${a/1e6:.1f}M"
    if a >= 1e4:
        return f"{s}${a/1e6:.2f}M"   # 与其它金额统一用 M，避免“$405,312”这种混排
    return f"{s}${a:,.0f}"


def color(x):
    return UP if (x or 0) > 0 else (DOWN if (x or 0) < 0 else "#666")


def is_cjk(s):
    return any("一" <= ch <= "鿿" for ch in s or "")


def clean_company(c):
    c = re.sub(r"[-\s]+(CL|CLASS)\s*[A-Z]\b.*$", "", c or "", flags=re.I)
    c = re.sub(r"\b(INC|CORP|CORPORATION|CO|LTD|PLC|LLC|HOLDINGS?|HLDGS?|GROUP|SA|NV|AG|ADR|ADS|SPONSORED)\b\.?",
               "", c, flags=re.I)
    c = re.sub(r"\s+", " ", c).strip(" ,.-")
    return c.title() if c.isupper() else c


def label_of(ticker, company):
    """图表坐标轴用的短标签：中文名（有）> 代码 > 公司名简写。"""
    cn = TICKER_CN.get((ticker or "").upper())
    if cn and is_cjk(cn):
        return cn
    if ticker:
        return ticker.upper()
    up = (company or "").upper()
    for k, v in COMPANY_CN.items():
        if k in up:
            return v
    return clean_company(company).split(" ")[0] or "?"


def full_name(ticker, company):
    cn = TICKER_CN.get((ticker or "").upper())
    if cn:
        return cn
    up = (company or "").upper()
    for k, v in COMPANY_CN.items():
        if k in up:
            return v
    return clean_company(company) or (ticker or "?")


# ---------------- charts ----------------
ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'


def js_boot(div, body):
    """等 echarts 加载后在 div 上初始化图表并执行 body（body 内可用变量 ch）。"""
    return ("<script>\n(function(){function draw(){var el=document.getElementById('" + div + "');"
            "if(!el||!window.echarts)return;var ch=echarts.init(el);" + body +
            "window.addEventListener('resize',function(){ch.resize();});}"
            "if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);"
            "setTimeout(function(){clearInterval(t);},8000);}})();\n</script>")


def kpi_cards(stats):
    # 卡片列数：4 张 → 2×2，3 张 → 一行三张；手机上 min-width 使其自动变一列
    n = len(stats)
    basis = "calc(50% - 6px)" if n in (2, 4) else ("calc(33.33% - 8px)" if n == 3 else "200px")
    cards = []
    for s in stats:
        if s.get("ret") is not None:
            big = f'<div style="font-size:26px;font-weight:700;color:{color(s["ret"])};margin:4px 0 6px;">{s["ret"]:+.2f}%</div>'
        else:
            big = '<div style="font-size:18px;color:#999;margin:6px 0 8px;">本周涨跌 —</div>'
        lines = []
        if s.get("pnl") is not None:
            lines.append(f'本周估算盈亏 <b style="color:{color(s["pnl"])}">{money(s["pnl"], True)}</b>')
        aum = f'规模 {money(s["aum"])}'
        if s.get("daum") is not None:
            aum += (f'（较上周 <b style="color:{color(s["daum"])}">{money(s["daum"], True)} / '
                    f'{s["daum_pct"]:+.1f}%</b>）')
        lines.append(aum)
        if s.get("daum") is not None and s.get("pnl") is not None:
            flow = s["daum"] - s["pnl"]   # 规模变化 − 价格盈亏 ≈ 净申赎（资金流）
            lines.append(f'估算净申赎 <b style="color:{color(flow)}">{money(flow, True)}</b>')
        lines.append(f'{s["n"]} 只持仓 · 第一大 {h(s["top"])} {s["top_w"]:.1f}%')
        cards.append(
            f'<div style="box-sizing:border-box;flex:1 1 {basis};min-width:200px;border:1px solid #e6e8eb;border-radius:10px;'
            'padding:12px 16px;background:#fafbfc;">'
            f'<div style="font-weight:700;font-size:15px;">{s["code"]} '
            f'<span style="color:#888;font-weight:400;font-size:13px;">{h(s["name"])}</span></div>'
            f'{big}<div style="font-size:13px;color:#555;line-height:1.85;">{"<br>".join(lines)}</div></div>')
    return '<div style="display:flex;flex-wrap:wrap;gap:12px;margin:10px 0 6px;">' + "".join(cards) + "</div>"


def weight_chart(fund, rows, prev, qtr, pdate, qdate):
    """三栏对齐：当前权重 | 较上周(pp) | 较上季度(pp)。prev/qtr: {key: weight}，空表示无数据。"""
    div = f"ark_w_{fund.lower()}"
    top = rows[:TOP_WEIGHT]
    names, cur, dw, dq, nw, nq, info = [], [], [], [], [], [], []
    for r in top:
        w = r["weight"]
        lab = label_of(r["ticker"], r["company"])
        d1 = n1 = d2 = n2 = None
        if prev:
            pw = prev.get(r["key"])
            d1, n1 = (round(w - pw, 2), False) if pw is not None else (round(w, 2), True)
        if qtr:
            qw = qtr.get(r["key"])
            d2, n2 = (round(w - qw, 2), False) if qw is not None else (round(w, 2), True)
        tip = f'<b>{h(full_name(r["ticker"], r["company"]))}</b> {h(r["ticker"] or "")}<br/>权重 {w:.2f}%'
        if d1 is not None:
            tip += "<br/>较上周 " + ("新建仓" if n1 else f"{d1:+.2f} 个百分点")
        if d2 is not None:
            tip += "<br/>较上季度 " + ("新建仓" if n2 else f"{d2:+.2f} 个百分点")
        tip += f'<br/>持股 {fmt_int(r["shares"])} · 市值 {money(r["mv"])}'
        names.append(lab); cur.append(round(w, 2)); dw.append(d1); dq.append(d2)
        nw.append(bool(n1)); nq.append(bool(n2)); info.append(tip)
    # 反转：最大的在最上面
    names, cur, dw, dq, nw, nq, info = (x[::-1] for x in (names, cur, dw, dq, nw, nq, info))

    def items(vals):
        return [{"value": v, "label": {"position": "left" if (v is not None and v < 0) else "right"}} for v in vals]

    m1 = max([abs(v) for v in dw if v is not None] + [0.05]) * 1.8
    m2 = max([abs(v) for v in dq if v is not None] + [0.05]) * 1.8
    t1 = f"较上周 {pdate[5:].replace('-', '/')}" if (prev and pdate) else "较上周（无数据）"
    t2 = f"较上季度 {qdate[5:].replace('-', '/')}" if (qtr and qdate) else "较上季度（无数据）"
    payload = json.dumps({"names": names, "cur": cur, "dw": dw, "dq": dq, "nw": nw, "nq": nq,
                          "dwi": items(dw), "dqi": items(dq), "info": info,
                          "m1": round(m1, 3), "m2": round(m2, 3), "t1": t1, "t2": t2}, ensure_ascii=False)
    tip = "tooltip:{trigger:'item',formatter:function(p){return D.info[p.dataIndex];}},"
    yl = "axisTick:{show:false},axisLine:{show:false},axisLabel:{fontSize:11,color:'#333'}"
    body = (
        "var D=" + payload + ";"
        "function lbl(a,n){return function(p){var v=a[p.dataIndex];if(v===null||v===undefined)return '';"
        "if(n[p.dataIndex])return '新建';return (v>0?'+':'')+v.toFixed(2);};}"
        "function col(p){return p.value>0?'" + UP + "':'" + DOWN + "';}"
        "function seg(a,n,i,tag){var v=a[i];if(v===null||v===undefined)return '';"
        "if(n[i])return '{nw|'+tag+'新建}';return (v>0?'{up|':'{dn|')+tag+(v>0?'+':'')+v.toFixed(2)+'}';}"
        "var zero={silent:true,symbol:'none',label:{show:false},lineStyle:{color:'#ccc',type:'solid'},data:[{xAxis:0}]};"
        "var ts={fontSize:12,color:'#555',fontWeight:'normal'};"
        # 宽屏：三栏对齐（当前权重 | 较上周 | 较上季度）
        "function wide(){return {" + tip +
        "title:[{text:'当前权重',left:56,top:0,textStyle:ts},{text:D.t1,left:'62%',top:0,textStyle:ts},"
        "{text:D.t2,left:'82%',top:0,textStyle:ts}],"
        "grid:[{left:56,width:'38%',top:26,bottom:6},{left:'62%',width:'15%',top:26,bottom:6},"
        "{left:'82%',width:'15%',top:26,bottom:6}],"
        "xAxis:[{gridIndex:0,type:'value',show:false},{gridIndex:1,type:'value',show:false,min:-D.m1,max:D.m1},"
        "{gridIndex:2,type:'value',show:false,min:-D.m2,max:D.m2}],"
        "yAxis:[{gridIndex:0,type:'category',data:D.names," + yl + "},"
        "{gridIndex:1,type:'category',data:D.names,show:false},{gridIndex:2,type:'category',data:D.names,show:false}],"
        "series:[{type:'bar',xAxisIndex:0,yAxisIndex:0,data:D.cur,barMaxWidth:16,"
        "itemStyle:{color:'" + BLUE + "',borderRadius:[0,3,3,0]},label:{show:true,position:'right',fontSize:10,formatter:'{c}%'}},"
        "{type:'bar',xAxisIndex:1,yAxisIndex:1,data:D.dwi,barMaxWidth:12,itemStyle:{color:col},markLine:zero,"
        "label:{show:true,fontSize:10,formatter:lbl(D.dw,D.nw)}},"
        "{type:'bar',xAxisIndex:2,yAxisIndex:2,data:D.dqi,barMaxWidth:12,itemStyle:{color:col},markLine:zero,"
        "label:{show:true,fontSize:10,formatter:lbl(D.dq,D.nq)}}]};}"
        # 窄屏（手机）：单栏，标签里用绿/红字标出 周/季 权重变化，避免三栏挤压重叠
        "function narrow(){return {" + tip +
        "title:[{text:'当前权重（标签：周 / 季 权重变化，百分点）',left:56,top:0,textStyle:ts}],"
        "grid:[{left:56,right:8,top:26,bottom:6}],"
        "xAxis:[{type:'value',show:false,max:function(v){return v.max*1.9;}}],"
        "yAxis:[{type:'category',data:D.names," + yl + "}],"
        "series:[{type:'bar',data:D.cur,barMaxWidth:14,itemStyle:{color:'" + BLUE + "',borderRadius:[0,3,3,0]},"
        "label:{show:true,position:'right',fontSize:10,color:'#333',"
        "formatter:function(p){var i=p.dataIndex;return p.value+'%  '+seg(D.dw,D.nw,i,'周')+'  '+seg(D.dq,D.nq,i,'季');},"
        "rich:{up:{color:'" + UP + "',fontSize:10},dn:{color:'" + DOWN + "',fontSize:10},nw:{color:'#999',fontSize:10}}}}]};}"
        "var isN=el.clientWidth<600;ch.setOption(isN?narrow():wide());"
        "window.addEventListener('resize',function(){var n2=el.clientWidth<600;"
        "if(n2!==isN){isN=n2;ch.setOption(isN?narrow():wide(),true);}});")
    height = 36 + 26 * len(names)
    return (f'<div id="{div}" style="letter-spacing:0;width:100%;max-width:860px;margin:6px auto 18px;height:{height}px;"></div>\n'
            + js_boot(div, body))


def trades_chart(fund, week):
    """本周净买卖（占基金净值 %）：发散柱，绿=净买入，红=净卖出。"""
    if not week:
        return '<p style="color:#999;margin:4px 0 18px;">本周无交易。</p>'
    div = f"ark_t_{fund.lower()}"
    items = list(reversed(week[:TOP_TRADES]))
    names = [label_of(x["ticker"], x["company"]) for x in items]
    vals = [round(x["pct"], 3) for x in items]
    info = [f'<b>{h(full_name(x["ticker"], x["company"]))}</b> {h(x["ticker"])}<br/>'
            f'本周净{"买入" if x["pct"] > 0 else "卖出"} {abs(x["pct"]):.2f}% 净值 · {fmt_int(abs(x["dshares"]))} 股'
            for x in items]
    m = max([abs(v) for v in vals] + [0.05]) * 1.4
    data = [{"value": v, "label": {"position": "left" if v < 0 else "right"}} for v in vals]
    payload = json.dumps({"names": names, "data": data, "info": info, "m": round(m, 3)}, ensure_ascii=False)
    body = (
        "var T=" + payload + ";"
        "ch.setOption({tooltip:{trigger:'item',formatter:function(p){return T.info[p.dataIndex];}},"
        "grid:{left:56,right:28,top:6,bottom:6},xAxis:{type:'value',show:false,min:-T.m,max:T.m},"
        "yAxis:{type:'category',data:T.names,axisTick:{show:false},axisLine:{show:false},axisLabel:{fontSize:11,color:'#333'}},"
        "series:[{type:'bar',data:T.data,barMaxWidth:14,"
        "itemStyle:{color:function(p){return p.value>0?'" + UP + "':'" + DOWN + "';}},"
        "markLine:{silent:true,symbol:'none',label:{show:false},lineStyle:{color:'#ccc',type:'solid'},data:[{xAxis:0}]},"
        "label:{show:true,fontSize:10,formatter:function(p){var v=p.value;return (v>0?'+':'')+v.toFixed(2)+'%';}}}]});")
    height = 16 + 26 * len(names)
    return (f'<div id="{div}" style="letter-spacing:0;width:100%;max-width:860px;margin:6px auto 18px;height:{height}px;"></div>\n'
            + js_boot(div, body))


def nearest_close(pmap, dates_sorted, day):
    import bisect
    i = bisect.bisect_right(dates_sorted, day) - 1
    return (dates_sorted[i], pmap[dates_sorted[i]]) if i >= 0 else None


def close_on(prices, day):
    best = None
    for p in prices:
        if p["d"] <= day:
            best = p
        else:
            break
    return (best["d"], best["c"]) if best else None


def price_chart(div, title, prices, trades):
    """价格曲线 + 该基金买卖点（绿 B / 红 S 实心圆，覆盖曲线；只标成交量最大的若干笔）。"""
    dates = [p["d"] for p in prices]
    closes = [p["c"] for p in prices]
    pmap = {p["d"]: p["c"] for p in prices}
    pts = []
    for tr in trades:
        np_ = nearest_close(pmap, dates, tr["date"])
        if np_:
            pts.append({"d": tr["date"], "value": [np_[0], np_[1]], "shares": int(tr["dshares"])})
    pts.sort(key=lambda p: -abs(p["shares"]))
    pts = pts[:24]
    buys = [dict(p, bs="B") for p in pts if p["shares"] > 0]
    sells = [dict(p, bs="S") for p in pts if p["shares"] < 0]
    payload = json.dumps({"dates": dates, "closes": closes, "buys": buys, "sells": sells}, ensure_ascii=False)
    body = (
        "var D=" + payload + ";"
        "function sz(v,p){var s=Math.abs(p.data.shares||0);return Math.max(16,Math.min(26,14+Math.log(s+10)/Math.LN10*2));}"
        "function mk(arr,color){return {type:'scatter',symbol:'circle',z:5,symbolSize:sz,"
        "itemStyle:{color:color,borderColor:'#fff',borderWidth:1.2},"
        "data:arr.map(function(o){return {value:o.value,shares:o.shares,d:o.d,bs:o.bs};}),"
        "label:{show:true,position:'inside',color:'#fff',fontWeight:'bold',fontSize:11,formatter:function(p){return p.data.bs;}},"
        "tooltip:{trigger:'item',formatter:function(p){var s=p.data.shares;return p.data.d+'<br/>'+"
        "(s>0?'买入 B  +':'卖出 S  ')+Math.abs(s).toLocaleString()+' 股';}}};}"
        "ch.setOption({grid:{left:8,right:16,top:16,bottom:24,containLabel:true},tooltip:{trigger:'axis'},"
        "xAxis:{type:'category',data:D.dates,axisLabel:{fontSize:10}},"
        "yAxis:{type:'value',scale:true,axisLabel:{formatter:'${value}'}},"
        "series:[{type:'line',data:D.closes,showSymbol:false,smooth:true,lineStyle:{width:2,color:'" + BLUE + "'},"
        "name:'收盘价',z:1},mk(D.buys,'" + UP + "'),mk(D.sells,'" + DOWN + "')]});")
    return (f'<p style="margin:14px 0 2px;font-weight:600;">{h(title)}</p>\n'
            f'<div id="{div}" style="letter-spacing:0;width:100%;max-width:860px;margin:0 auto 20px;height:320px;"></div>\n'
            + js_boot(div, body))


# ---------------- markdown ----------------
def build_markdown(data_date, funds, stats, week_from):
    dt = datetime.date.fromisoformat(data_date)
    wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
    codes = [c for c in SHOW if c in funds]
    any_f = funds[codes[0]]
    fm = ["---", "layout:     post",
          f'title:      "Cathie Wood / ARK 每周持仓追踪 ({data_date})"',
          f'subtitle:   "{"·".join(codes)} 本周涨跌、权重变化、买卖点 · 数据源：ARK 官方披露"',
          f"date:       {data_date}", 'author:     "龟龟"', 'header-img: "/img/home-bg.jpg"',
          "catalog:    true", "tags:", "    - 投资", "    - Cathie Wood", "    - ARK", "    - 持仓追踪", "---", "",
          "> 🤖 **每周自动更新：数据截至周五收盘**（ARK 下周一披露周五收盘持仓后生成）。数据来自 ARK Invest 官方每日全持仓披露、arkfunds.io 与 "
          "Yahoo Finance 价格，均为公开信息；本文为基于公开数据的原创整理，**非投资建议**。选题线索来自 "
          "[Moomoo Whale Watch](https://www.moomoo.com/quote/institution-tracking)（仅作线索与致谢，未使用其文章内容）。",
          "",
          f"**数据日期：{data_date}（{wd}收盘）** ｜ 对比上周：{any_f.get('pdate') or '—'} ｜ "
          f"对比上季度：{any_f.get('qdate') or '—'}", ""]
    body = [
        '<div id="gemini-review" style="border-left:4px solid #4285F4;background:#eef4ff;padding:14px 16px;margin:0 0 22px;border-radius:8px;">',
        '<strong>🔷 Gemini 简评</strong>',
        '<!-- GEMINI_COMMENT_START -->',
        '<p style="color:#999;margin:8px 0 0;">（简评待生成：由 Gemini 自动追加）</p>',
        '<!-- GEMINI_COMMENT_END -->',
        '</div>', "", ECHARTS_CDN, "",
        "## 本周概览", "", kpi_cards(stats), "",
        '<p style="font-size:12px;color:#999;margin:4px 0 18px;">注：所有数据均按收盘口径（上周收盘→本周收盘），本周涨跌按 ETF 收盘价；'
        '估算盈亏＝上周规模×本周涨跌（不含申赎）；规模＝持仓市值合计；估算净申赎＝规模变化−估算盈亏（资金净流入为正）。</p>', ""]
    for c in codes:
        f = funds[c]
        body += [f"## {c} · {f['name']}", "",
                 f"**持仓权重 Top{TOP_WEIGHT}**　并列较上周（{f.get('pdate') or '—'}）、较上季度（{f.get('qdate') or '—'}）"
                 f"的权重增减（百分点；🟢增 🔴减；“新建”=当时未持有）", "",
                 weight_chart(c, f["rows"], f["prev_w"], f["qtr_w"], f.get("pdate"), f.get("qdate")), "",
                 f"**本周净买卖**　{week_from.get(c) or '—'} 之后至 {data_date}，按占基金净值 %（🟢买入 🔴卖出）", "",
                 trades_chart(c, f["week"]), ""]
    body += ["## 价格曲线 · 买卖点", "",
             "> 各基金前 5 大持仓的近两年收盘价；🟢 **B**=买入、🔴 **S**=卖出（该基金自己的交易；圆点大小≈交易量，"
             "只标成交量最大的若干笔；悬停可看日期与股数）。", ""]
    for c in codes:
        f = funds[c]
        body += [f"### {c} 前 {TOP_PRICE} 大持仓", ""] + f["price_blocks"]
        if f["price_skipped"]:
            body += [f"> 无公开价格已跳过：{', '.join(f['price_skipped'])}", ""]
    body += ["---", "",
             "*本页由脚本依据 ARK 官方公开持仓、arkfunds.io 与 Yahoo 公开价格自动生成，仅供研究记录，不构成任何投资建议。"
             "估算盈亏为按公开价格的粗略估计，以 ARK 官方披露为准。*"]
    return "\n".join(fm + body) + "\n"


SPEC_TEXT = """# ark-data 数据说明（RENDERING SPEC）

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
"""


def load_snapshot(fund):
    """回退：本地上次快照（ARK 官方 CSV）-> (date, {key: {...}})。"""
    p = os.path.join(STATE_DIR, fund + ".csv")
    if not os.path.exists(p):
        return None, {}
    d, rows = parse_holdings(open(p, encoding="utf-8").read())
    if not d:
        return None, {}
    di = datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat()
    return di, {hkey(r["ticker"], r["cusip"], r["company"]): {"weight": r["weight"], "shares": r["shares"],
                                                              "mv": r["mv"], "company": r["company"]} for r in rows}


def main():
    force = "--force" in sys.argv
    m = re.search(r"--date[= ](\d{4}-\d{2}-\d{2})\b", " ".join(sys.argv[1:]))
    backfill = m.group(1) if m else None      # 补做过去某周：持仓取 arkfunds 历史，不动 state/ 与 last_date
    for d in (STATE_DIR, POSTS_DIR, SIDECAR_DIR):
        os.makedirs(d, exist_ok=True)
    td = trading_days()

    # 1) 定本期“周收盘日”W，并取 W 收盘时的持仓
    #    常规：ARK 官方 CSV（文件日 F 记录 F 前一交易日 C 的收盘）；C 是当周最后一个交易日才可直接用，
    #    否则（如周末时 CSV 还是周五文件＝周四收盘）本期取上周收盘，持仓改从 arkfunds 历史取。
    fresh = {}
    if backfill:
        W = last_td(td, backfill)
    else:
        for code in SHOW:
            name, fn = FUNDS[code]
            try:
                raw = fetch_text(ARK_BASE + fn)
                d, rows = parse_holdings(raw)
                if d and rows:
                    fresh[code] = {"name": name, "date": datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat(),
                                   "rows": rows, "raw": raw}
                else:
                    print(f"[skip] {code} no rows")
            except Exception as e:
                print(f"[skip] {code} {e}")
        if not fresh:
            print("NO_DATA")
            return 2
        F = max(v["date"] for v in fresh.values())
        fresh = {c: v for c, v in fresh.items() if v["date"] == F}
        C = prev_td(td, F)
        wk = lambda s: datetime.date.fromisoformat(s).isocalendar()[:2]
        W = C if (C and wk(C) != wk(F)) else prev_week_close(td, F)
        print(f"[info] ARK CSV 文件日 {F}（记录 {C} 收盘）-> 本期周收盘 {W}")
        if W != C:
            fresh = {}
    if not fresh:
        for code in SHOW:
            try:
                d, rows = fetch_snapshot_rows(code, W)
            except Exception as e:
                d, rows = None, []
                print(f"[skip] {code} {e}")
            if d and rows:
                if prev_td(td, d) != W:
                    print(f"[warn] {code} {W} 之后第一份文件是 {d}（中间缺披露），持仓可能已含之后的交易")
                fresh[code] = {"name": FUNDS[code][0], "date": d, "rows": rows, "raw": None}
        if not fresh:
            print(f"SNAPSHOT_NOT_READY: {W} 收盘的持仓尚未披露（要等其后第一份 ARK 文件）")
            return 0
    data_date = W
    for c, v in fresh.items():
        print(f"[ok]   {c} 文件 {v['date']} rows={len(v['rows'])}")
    print(f"[info] data_date={data_date}（收盘） funds={list(fresh)}" + (f" (补做 {backfill})" if backfill else ""))

    last_file = os.path.join(STATE_DIR, "last_date.txt")
    last = open(last_file).read().strip() if os.path.exists(last_file) else None
    if last == data_date and not force and not backfill:
        print("NO_NEW_DATA")
        return 0

    dW = datetime.date.fromisoformat(data_date)
    week_close = prev_week_close(td, data_date)                                   # 上周收盘（通常上周五）
    qtr_close = last_td(td, (dW - datetime.timedelta(days=91)).isoformat())       # 约 13 周前收盘
    since = (dW - datetime.timedelta(days=740)).isoformat()

    funds, week_from, price_cache = {}, {}, {}
    for code, v in fresh.items():
        rows = sorted(({**r, "key": hkey(r["ticker"], r["cusip"], r["company"])} for r in v["rows"]),
                      key=lambda r: -r["weight"])
        aum = sum(r["mv"] for r in rows)

        # 2) 上周 / 上季度收盘时的持仓（arkfunds 历史；上周失败则回退本地快照）
        pdate, (_, prev) = week_close, fetch_snapshot(code, week_close)
        if not prev:
            sd, snap = load_snapshot(code)
            if snap and sd and prev_td(td, sd) == week_close:
                prev = snap
                print(f"[fallback] {code} 上周用本地快照（文件 {sd}）")
            else:
                pdate = None
        qdate, (_, qtr) = qtr_close, fetch_snapshot(code, qtr_close)
        qdate = qdate if qtr else None
        aum_prev = sum(x["mv"] for x in prev.values()) if prev else None

        # 3) ETF 本周涨跌 & 估算盈亏（与两次持仓快照同一窗口：上周收盘 -> 本周收盘）
        ret = pnl = None
        px = fetch_prices(code, "1y")
        if px and pdate:
            a, b = close_on(px, pdate), close_on(px, data_date)
            if a and b and a[1] and a[0] == pdate and b[0] == data_date:
                ret = (b[1] / a[1] - 1) * 100
        if ret is not None:
            pnl = (aum_prev if aum_prev else aum / (1 + ret / 100)) * ret / 100
        daum = (aum - aum_prev) if aum_prev else None
        daum_pct = (daum / aum_prev * 100) if aum_prev else None

        # 4) 交易：近两年（买卖点）+ 本周净买卖；截到数据日（补做过去某周时不混入之后的交易）
        trades = [x for x in (fetch_trades(code, since) or []) if x["date"] <= data_date]
        w0 = pdate or week_close
        week_from[code] = w0
        agg = {}
        for x in trades:
            if w0 < x["date"] <= data_date:
                a = agg.setdefault(x["ticker"], {"ticker": x["ticker"], "company": x["company"], "pct": 0.0, "dshares": 0})
                a["pct"] += x["pct"]
                a["dshares"] += x["dshares"]
        week = sorted((a for a in agg.values() if abs(a["pct"]) >= 0.005), key=lambda a: -abs(a["pct"]))  # <0.005% 显示为 0.00，视为噪声

        # 5) 前 5 大持仓价格曲线（该基金自己的买卖点）
        by_t = {}
        for x in trades:
            dd = by_t.setdefault(x["ticker"], {})
            dd[x["date"]] = dd.get(x["date"], 0) + x["dshares"]
        blocks, skipped = [], []
        for r in rows:
            if len(blocks) >= TOP_PRICE:
                break
            t = (r["ticker"] or "").upper()
            if not t:
                continue
            if t not in price_cache:
                price_cache[t] = fetch_prices(t, "2y")
            p = [x for x in price_cache[t] if x["d"] <= data_date]   # 曲线止于数据日
            if not p:
                skipped.append(t)
                continue
            tl = [{"date": dd, "dshares": vv} for dd, vv in sorted(by_t.get(t, {}).items()) if abs(vv) >= 1]
            title = (f"{full_name(t, r['company'])} · {t} — {code} 持有 {fmt_int(r['shares'])} 股"
                     f"（权重 {r['weight']:.2f}%）")
            blocks.append(price_chart(f"ark_px_{code.lower()}_{re.sub(r'[^a-z0-9]', '_', t.lower())}", title, p, tl))

        funds[code] = {"name": v["name"], "rows": rows, "aum": aum, "aum_prev": aum_prev, "daum": daum,
                       "daum_pct": daum_pct, "ret": ret, "pnl": pnl, "pdate": pdate, "qdate": qdate,
                       "prev_w": {k: x["weight"] for k, x in prev.items()},
                       "qtr_w": {k: x["weight"] for k, x in qtr.items()},
                       "week": week, "price_blocks": blocks, "price_skipped": skipped, "raw": v["raw"]}
        print(f"[fund] {code} aum={money(aum)} ret={ret} pnl={pnl and money(pnl, True)} "
              f"prev={pdate} qtr={qdate} week_trades={len(week)} price_charts={len(blocks)}")

    codes = [c for c in SHOW if c in funds]
    stats = []
    for c in codes:
        f = funds[c]
        top = f["rows"][0]
        stats.append({"code": c, "name": f["name"], "ret": f["ret"], "pnl": f["pnl"], "aum": f["aum"],
                      "daum": f["daum"], "daum_pct": f["daum_pct"], "n": len(f["rows"]),
                      "top": label_of(top["ticker"], top["company"]), "top_w": top["weight"]})

    # 6) sidecar（供 Gemini 简评）
    sidecar = {"date": data_date, "generated_at": datetime.datetime.now().isoformat(timespec="seconds"), "funds": {}}
    for c in codes:
        f = funds[c]
        top = []
        for r in f["rows"][:10]:
            pw, qw = f["prev_w"].get(r["key"]), f["qtr_w"].get(r["key"])
            top.append({"ticker": r["ticker"], "label": label_of(r["ticker"], r["company"]),
                        "weight": round(r["weight"], 2),
                        "d_week": (round(r["weight"] - pw, 2) if pw is not None else round(r["weight"], 2)) if f["prev_w"] else None,
                        "d_quarter": (round(r["weight"] - qw, 2) if qw is not None else round(r["weight"], 2)) if f["qtr_w"] else None})
        mk = lambda x: {"ticker": x["ticker"], "label": label_of(x["ticker"], x["company"]),
                        "pct": round(x["pct"], 3), "shares": x["dshares"]}
        sidecar["funds"][c] = {
            "name": f["name"], "aum": round(f["aum"]),
            "aum_prev": round(f["aum_prev"]) if f["aum_prev"] is not None else None,
            "daum_pct": round(f["daum_pct"], 2) if f["daum_pct"] is not None else None,
            "ret_pct": round(f["ret"], 2) if f["ret"] is not None else None,
            "pnl": round(f["pnl"]) if f["pnl"] is not None else None,
            "flow": round(f["daum"] - f["pnl"]) if (f["daum"] is not None and f["pnl"] is not None) else None,
            "prev_date": f["pdate"], "quarter_date": f["qdate"], "top": top,
            "week_trades": {"buys": [mk(x) for x in f["week"] if x["pct"] > 0][:8],
                            "sells": [mk(x) for x in f["week"] if x["pct"] < 0][:8]}}

    md = build_markdown(data_date, funds, stats, week_from)
    # 一次成文：配了 GEMINI_API_KEY 就把 Gemini 简评内嵌进正文（无 key/失败则保留占位符，不影响发帖）
    try:
        import gemini_review as gr
        rev = gr.build_review_html("ark", sidecar)
        if rev:
            md = gr.fill_slot(md, rev)
            print("[gemini] 简评已内嵌")
    except Exception as e:
        print("[gemini-skip]", e)

    out_path = os.path.join(POSTS_DIR, f"{data_date}-ark-cathie-wood.markdown")
    open(out_path, "w", encoding="utf-8").write(md)
    open(os.path.join(SIDECAR_DIR, f"{data_date}.json"), "w", encoding="utf-8").write(
        json.dumps(sidecar, ensure_ascii=False, indent=2))
    open(SPEC_PATH, "w", encoding="utf-8").write(SPEC_TEXT)
    if not backfill:   # 补做过去某周不动“最新”状态
        for c in codes:   # 本地快照（上周回退用；本期持仓来自 arkfunds 时没有原始 CSV，保留旧快照）
            if funds[c]["raw"]:
                open(os.path.join(STATE_DIR, c + ".csv"), "w", encoding="utf-8").write(funds[c]["raw"])
        open(last_file, "w", encoding="utf-8").write(data_date)
    print("POST:" + os.path.relpath(out_path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
