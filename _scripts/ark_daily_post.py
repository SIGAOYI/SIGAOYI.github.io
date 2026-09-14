#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cathie Wood / ARK 每日持仓追踪 -> Jekyll 文章自动发布

- 数据源：ARK Invest 官方每日全持仓 CSV（公开、免费、可合法使用）。
- 写入 _posts/（Jekyll 会构建并发布到线上），内容为“原创分析”，不搬运任何第三方文章正文。
- 纯脚本、确定性、无 LLM、零成本。
- 每日变化对比上一交易日快照（存在 _scripts/state/，被 Jekyll 忽略但受 git 跟踪）。
- 护栏：数据日期未变 -> NO_NEW_DATA 跳过；已有基准且当日零变化 -> NO_CHANGES 跳过（不刷空帖）。

用法：
  python3 _scripts/ark_daily_post.py [--force]
  --force  忽略上述护栏强制生成一篇（首次/手动补发用）。

退出码：0=正常（可能是 NO_NEW_DATA / NO_CHANGES 跳过）；2=完全拉不到数据。
"""
import csv, io, os, sys, json, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # -> BLOG/
STATE_DIR = os.path.join(ROOT, "_scripts", "state")
POSTS_DIR = os.path.join(ROOT, "_posts")

BASE = "https://assets.ark-funds.com/fund-documents/funds-etf-csv/"
UA = "Mozilla/5.0 (compatible; ark-daily-draft/1.0; +https://axelrod.lawootrip.com)"

# 代码 -> (中文名, CSV 文件名)。拉不到/过期的会自动跳过。
FUNDS = {
    "ARKK": ("ARK 旗舰·颠覆式创新", "ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv"),
    "ARKW": ("下一代互联网",       "ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv"),
    "ARKG": ("基因革命",           "ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv"),
    "ARKQ": ("自动化与机器人",     "ARK_AUTONOMOUS_TECH._&_ROBOTICS_ETF_ARKQ_HOLDINGS.csv"),
    "ARKF": ("金融科技创新",       "ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv"),
    "ARKX": ("太空探索与创新",     "ARK_SPACE_EXPLORATION_&_INNOVATION_ETF_ARKX_HOLDINGS.csv"),
}
ORDER = ["ARKK", "ARKW", "ARKG", "ARKQ", "ARKF", "ARKX"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8-sig", errors="replace")


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
    """返回 (date_str_mmddyyyy, rows[])；rows: {company,ticker,cusip,shares,mv,weight}"""
    rdr = csv.reader(io.StringIO(text))
    header = None
    idx = {}
    rows = []
    date_str = None
    for raw in rdr:
        if not raw or all((c or "").strip() == "" for c in raw):
            continue
        if header is None:
            header = [(c or "").strip().lower() for c in raw]
            for key in ("date", "company", "ticker", "cusip", "shares"):
                for i, h in enumerate(header):
                    if key in h:
                        idx[key] = i
                        break
            for i, h in enumerate(header):
                if "market" in h and "value" in h:
                    idx["mv"] = i
                if "weight" in h:
                    idx["weight"] = i
            continue

        def cell(k):
            i = idx.get(k)
            return raw[i].strip() if (i is not None and i < len(raw)) else ""

        d = cell("date")
        comp = cell("company")
        if not d or "/" not in d or not comp:
            continue  # 跳过页尾免责声明等非数据行
        if date_str is None:
            date_str = d
        sh = num(cell("shares"))
        w = num(cell("weight"))
        if sh is None and w is None:
            continue
        rows.append({
            "company": comp,
            "ticker": cell("ticker"),
            "cusip": cell("cusip"),
            "shares": sh or 0.0,
            "mv": num(cell("mv")) or 0.0,
            "weight": w or 0.0,
        })
    return date_str, rows


def key_of(r):
    return r["ticker"] or r["cusip"] or r["company"]


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
            base = prev[k]["shares"] or 1
            pct = d / base * 100.0
            rec = dict(r); rec["dshares"] = d; rec["dpct"] = pct
            (inc if d > 0 else dec).append(rec)
    for k, r in prev.items():
        if k not in cur:
            exited.append(r)
    new.sort(key=lambda x: -x["weight"])
    exited.sort(key=lambda x: -x["mv"])
    inc.sort(key=lambda x: -x["dpct"])
    dec.sort(key=lambda x: x["dpct"])
    return {"new": new, "exited": exited, "inc": inc, "dec": dec}


def h(s):  # HTML escape for text cells
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def top_table(rows, n=15, with_shares=True):
    out = ['<table style="width:100%;border-collapse:collapse;font-size:14px;">',
           '<thead><tr style="text-align:left;border-bottom:2px solid #ccc;">'
           '<th>#</th><th>公司</th><th>代码</th>'
           + ('<th style="text-align:right;">股数</th>' if with_shares else '')
           + '<th style="text-align:right;">市值</th><th style="text-align:right;">权重</th></tr></thead><tbody>']
    for i, r in enumerate(rows[:n], 1):
        out.append(
            f'<tr style="border-bottom:1px solid #eee;"><td>{i}</td>'
            f'<td>{h(r["company"])}</td><td>{h(r["ticker"])}</td>'
            + (f'<td style="text-align:right;">{fmt_int(r["shares"])}</td>' if with_shares else '')
            + f'<td style="text-align:right;">{fmt_mv(r["mv"])}</td>'
            f'<td style="text-align:right;">{r["weight"]:.2f}%</td></tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def change_table(rows, kind):
    if not rows:
        return "<p><em>无</em></p>"
    if kind in ("new", "exited"):
        cols = '<th>公司</th><th>代码</th><th style="text-align:right;">股数</th><th style="text-align:right;">权重</th>'
        body = ""
        for r in rows[:15]:
            body += (f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["company"])}</td>'
                     f'<td>{h(r["ticker"])}</td><td style="text-align:right;">{fmt_int(r["shares"])}</td>'
                     f'<td style="text-align:right;">{r["weight"]:.2f}%</td></tr>')
    else:
        cols = ('<th>公司</th><th>代码</th><th style="text-align:right;">股数变化</th>'
                '<th style="text-align:right;">变化%</th><th style="text-align:right;">现权重</th>')
        body = ""
        for r in rows[:15]:
            sign = "+" if r["dshares"] > 0 else ""
            color = "#c0392b" if r["dshares"] > 0 else "#2e7d32"  # 红买绿卖(中式)
            body += (f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["company"])}</td>'
                     f'<td>{h(r["ticker"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{fmt_int(r["dshares"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{r["dpct"]:.1f}%</td>'
                     f'<td style="text-align:right;">{r["weight"]:.2f}%</td></tr>')
    return ('<table style="width:100%;border-collapse:collapse;font-size:14px;">'
            f'<thead><tr style="text-align:left;border-bottom:2px solid #ccc;">{cols}</tr></thead>'
            f'<tbody>{body}</tbody></table>')


def echarts_bar(fund_code, rows, n=15):
    data = [{"name": f'{r["ticker"] or r["company"]}', "value": round(r["weight"], 2)}
            for r in rows[:n]][::-1]  # 反转让最大在顶部
    div_id = f"ark_{fund_code.lower()}_top"
    payload = json.dumps(data, ensure_ascii=False)
    return (
        f'<div id="{div_id}" style="width:100%;max-width:860px;margin:18px auto;height:{max(360, 34*len(data))}px;"></div>\n'
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>\n'
        '<script>\n'
        '(function(){\n'
        f'  var raw={payload};\n'
        '  var names=raw.map(function(d){return d.name;});\n'
        '  var vals=raw.map(function(d){return d.value;});\n'
        f'  function draw(){{\n'
        f'    var el=document.getElementById("{div_id}");\n'
        '    if(!el||!window.echarts) return;\n'
        '    var ch=echarts.init(el);\n'
        '    ch.setOption({\n'
        '      grid:{left:8,right:56,top:10,bottom:10,containLabel:true},\n'
        '      tooltip:{trigger:"axis",axisPointer:{type:"shadow"},valueFormatter:function(v){return v+"%";}},\n'
        '      xAxis:{type:"value",axisLabel:{formatter:"{value}%"}},\n'
        '      yAxis:{type:"category",data:names,axisLabel:{fontSize:12}},\n'
        '      series:[{type:"bar",data:vals,barMaxWidth:22,\n'
        '        itemStyle:{color:"#c0392b",borderRadius:[0,4,4,0]},\n'
        '        label:{show:true,position:"right",formatter:"{c}%",fontSize:11}}]\n'
        '    });\n'
        '    window.addEventListener("resize",function(){ch.resize();});\n'
        '  }\n'
        '  if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);setTimeout(function(){clearInterval(t);},6000);}\n'
        '})();\n'
        '</script>'
    )


def build_markdown(fresh, diffs, data_date, pub_date, had_prev):
    dt = datetime.date.fromisoformat(data_date)
    codes = [c for c in ORDER if c in fresh]
    total_mv = sum(sum(r["mv"] for r in fresh[c]["rows"]) for c in codes)

    fm = [
        "---",
        "layout:     post",
        f'title:      "Cathie Wood / ARK 每日持仓追踪 ({data_date})"',
        f'subtitle:   "{"·".join(codes)} 全持仓快照与当日买卖变化 · 数据源：ARK 官方每日披露"',
        f"date:       {pub_date}",
        'author:     "龟龟"',
        'header-img: "/img/home-bg.jpg"',
        "catalog:    true",
        "tags:",
        "    - 投资",
        "    - Cathie Wood",
        "    - ARK",
        "    - 持仓追踪",
        "---",
        "",
        "> 🤖 **每交易日自动更新**。数据来自 ARK Invest 官方每日全持仓披露"
        "（assets.ark-funds.com），为公开信息；本文为基于公开数据的原创整理，"
        "**非投资建议**。选题线索来自 [Moomoo Whale Watch](https://www.moomoo.com/quote/institution-tracking)"
        "（仅作线索与致谢，未使用其文章内容）。",
        "",
        f"**数据日期：{data_date}（{['周一','周二','周三','周四','周五','周六','周日'][dt.weekday()]}）** ｜ "
        f"覆盖基金：{len(codes)} 只 ｜ 合计市值约 {fmt_mv(total_mv)}",
        "",
    ]

    body = ["## 当日概览", ""]
    for c in codes:
        rows = fresh[c]["rows"]
        mv = sum(r["mv"] for r in rows)
        top = max(rows, key=lambda r: r["weight"]) if rows else None
        line = (f'- **{c}**（{fresh[c]["name"]}）：{len(rows)} 只持仓，规模约 {fmt_mv(mv)}'
                + (f'，第一大重仓 **{top["ticker"] or top["company"]}**（{top["weight"]:.2f}%）' if top else ""))
        if had_prev and c in diffs:
            d = diffs[c]
            line += f'；当日 新建 {len(d["new"])} / 清仓 {len(d["exited"])} / 增持 {len(d["inc"])} / 减持 {len(d["dec"])}'
        body.append(line)
    body.append("")

    # 旗舰 ARKK 图表 + 明细
    if "ARKK" in fresh:
        rows = sorted(fresh["ARKK"]["rows"], key=lambda r: -r["weight"])
        body += ["## ARKK 旗舰：前 15 大重仓（按权重）", "", echarts_bar("ARKK", rows), "",
                 top_table(rows, 15), ""]

    # 当日变化
    body += ["## 当日买卖变化（对比上一交易日）", ""]
    if not had_prev:
        body += ["> 首次运行，已建立基准快照；**增持/减持/新建/清仓 将从下一交易日起自动出现。**", ""]
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

    # 其他基金明细
    others = [c for c in codes if c != "ARKK"]
    if others:
        body += ["## 其他 ARK 基金 · 前 8 大重仓", ""]
        for c in others:
            rows = sorted(fresh[c]["rows"], key=lambda r: -r["weight"])
            body += [f"### {c}（{fresh[c]['name']}）", "", top_table(rows, 8), ""]

    body += ["---",
             "",
             "*本页由脚本依据 ARK 官方公开每日持仓 CSV 自动生成，仅供研究记录，不构成任何投资建议。"
             "持仓与权重每日变动，以 ARK 官方披露为准。*"]

    return "\n".join(fm + body) + "\n"


def main():
    force = "--force" in sys.argv
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(POSTS_DIR, exist_ok=True)

    fetched = {}
    for code in ORDER:
        name, fn = FUNDS[code]
        try:
            txt = fetch(BASE + fn)
            d, rows = parse_holdings(txt)
            if d and rows:
                fetched[code] = {"name": name, "date": d, "rows": rows, "raw": txt}
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
    print(f"[info] newest date={data_date}; fresh funds={list(fresh)}")

    last_file = os.path.join(STATE_DIR, "last_date.txt")
    last = open(last_file).read().strip() if os.path.exists(last_file) else None
    if last == data_date and not force:
        print("NO_NEW_DATA")
        return 0

    # 计算 diff（对比 state 里的上一快照）
    had_prev = False
    diffs = {}
    for c, v in fresh.items():
        sp = os.path.join(STATE_DIR, c + ".csv")
        if os.path.exists(sp):
            _, prev_rows = parse_holdings(open(sp, encoding="utf-8").read())
            if prev_rows:
                diffs[c] = diff_fund(v["rows"], prev_rows)
                had_prev = True

    # 护栏：有基准且当日零变化 -> 不发帖（避免空帖刷屏）
    if had_prev and not force:
        total_changes = sum(len(d["new"]) + len(d["exited"]) + len(d["inc"]) + len(d["dec"])
                            for d in diffs.values())
        if total_changes == 0:
            print("NO_CHANGES")
            return 0

    # 用运行日作为发布日，避免 ARK 前瞻日期被 Jekyll future 过滤；数据日期在标题/正文中标注
    pub_date = datetime.date.today().isoformat()
    md = build_markdown(fresh, diffs, data_date, pub_date, had_prev)
    out_path = os.path.join(POSTS_DIR, f"{pub_date}-ark-cathie-wood.markdown")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)

    # 更新 state（覆盖为最新快照，供下次 diff）
    for c, v in fresh.items():
        with open(os.path.join(STATE_DIR, c + ".csv"), "w", encoding="utf-8") as f:
            f.write(v["raw"])
    with open(last_file, "w", encoding="utf-8") as f:
        f.write(data_date)

    print("POST:" + os.path.relpath(out_path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
