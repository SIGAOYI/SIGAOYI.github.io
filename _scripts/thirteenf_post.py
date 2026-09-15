#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资者 13F 季度持仓追踪 -> Jekyll 文章自动发布（段永平 / 李录）

- 数据源：SEC EDGAR 官方 13F-HR 申报（公开、免费）。13F 为季度报、滞后约 45 天。
- 写入 _posts/（直接发布）；纯脚本、确定性、无 LLM、零 token。
- 每次运行取各投资者最新一季 13F，对比上一季，渲染 Top 持仓条形图 + 明细 + 季度增减。
- 去重：按最新报告季（reportDate）。同季已发过则跳过（NO_NEW_QUARTER）。
- 合规：仅用 SEC 公开数据做原创整理；非投资建议。

用法：python3 _scripts/thirteenf_post.py [--force]
"""
import os, sys, re, json, datetime, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(ROOT, "_scripts", "state")
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
LAST_PATH = os.path.join(STATE_DIR, "13f_last_report.txt")
UA = {"User-Agent": "blog-research lawootrip@gmail.com"}

INVESTORS = [
    {"name": "段永平", "entity": "H&H International Investment", "slug": "duan-yongping", "cik": 1759760},
    {"name": "李录", "entity": "Himalaya Capital Management", "slug": "li-lu", "cik": 1709323},
]


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def fmt_money(v):
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.1f}M"
    return f"${v:,.0f}"


def fmt_int(x):
    try:
        return f"{int(round(x)):,}"
    except Exception:
        return str(x)


def h(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_infotable(xml):
    """13F infotable.xml -> {cusip: {issuer,cls,value,shares}}（按 cusip 聚合）。"""
    xml = re.sub(r'xmlns(:\w+)?="[^"]+"', '', xml)
    xml = re.sub(r'<(/?)\w+:', r'<\1', xml)
    root = ET.fromstring(xml)
    out = {}
    for it in root.findall(".//infoTable"):
        cusip = (it.findtext("cusip") or "").strip().upper()
        issuer = (it.findtext("nameOfIssuer") or "").strip()
        cls = (it.findtext("titleOfClass") or "").strip()
        try:
            value = float(it.findtext("value") or 0)
        except ValueError:
            value = 0.0
        sh = it.find("shrsOrPrnAmt")
        try:
            shares = float(sh.findtext("sshPrnamt") or 0) if sh is not None else 0.0
        except ValueError:
            shares = 0.0
        if not cusip:
            continue
        r = out.setdefault(cusip, {"issuer": issuer, "cls": cls, "value": 0.0, "shares": 0.0})
        r["value"] += value
        r["shares"] += shares
    return out


def fetch_13f(cik):
    """返回 (latest, prev)；每个 = {report, filed, holdings{cusip:..}} 或 None。"""
    j = json.loads(get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"))
    r = j["filings"]["recent"]
    idxs = [i for i, f in enumerate(r["form"]) if f == "13F-HR"]
    if not idxs:
        return None, None

    def load(i):
        acc = r["accessionNumber"][i].replace("-", "")
        base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
        li = json.loads(get(base + "/index.json"))
        xmls = [it["name"] for it in li["directory"]["item"] if it["name"].lower().endswith(".xml")]
        cands = [n for n in xmls if "primary_doc" not in n.lower()]
        cands.sort(key=lambda n: 0 if ("infotable" in n.lower() or "table" in n.lower() or "13f" in n.lower()) else 1)
        holdings = {}
        for n in cands:
            try:
                holdings = parse_infotable(get(f"{base}/{n}").decode("utf-8", "replace"))
                if holdings:
                    break
            except Exception:
                continue
        return {"report": r["reportDate"][i], "filed": r["filingDate"][i], "holdings": holdings}

    latest = load(idxs[0])
    prev = load(idxs[1]) if len(idxs) > 1 else None
    return latest, prev


def diff_13f(latest, prev):
    cur = latest["holdings"]
    if not prev:
        return None
    old = prev["holdings"]
    new, exited, inc, dec = [], [], [], []
    for c, r in cur.items():
        if c not in old:
            new.append(r)
        else:
            d = r["shares"] - old[c]["shares"]
            if abs(d) < 1:
                continue
            rec = dict(r); rec["dshares"] = d; rec["dpct"] = d / (old[c]["shares"] or 1) * 100
            (inc if d > 0 else dec).append(rec)
    for c, r in old.items():
        if c not in cur:
            exited.append(r)
    new.sort(key=lambda x: -x["value"]); exited.sort(key=lambda x: -x["value"])
    inc.sort(key=lambda x: -x["dpct"]); dec.sort(key=lambda x: x["dpct"])
    return {"new": new, "exited": exited, "inc": inc, "dec": dec}


ECHARTS_CDN = '<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>'


def bar_chart(div, rows, total, n=12):
    data = [{"name": r["issuer"][:18], "value": round(r["value"] / total * 100, 2)} for r in rows[:n]][::-1]
    payload = json.dumps(data, ensure_ascii=False)
    js = ("(function(){var raw=" + payload + ";var names=raw.map(function(d){return d.name;});var vals=raw.map(function(d){return d.value;});"
          "function draw(){var el=document.getElementById('" + div + "');if(!el||!window.echarts)return;var ch=echarts.init(el);"
          "ch.setOption({grid:{left:8,right:56,top:10,bottom:10,containLabel:true},"
          "tooltip:{trigger:'axis',axisPointer:{type:'shadow'},valueFormatter:function(v){return v+'%';}},"
          "xAxis:{type:'value',axisLabel:{formatter:'{value}%'}},yAxis:{type:'category',data:names,axisLabel:{fontSize:12}},"
          "series:[{type:'bar',data:vals,barMaxWidth:22,itemStyle:{color:'#2f6f4f',borderRadius:[0,4,4,0]},"
          "label:{show:true,position:'right',formatter:'{c}%',fontSize:11}}]});"
          "window.addEventListener('resize',function(){ch.resize();});}"
          "if(window.echarts){draw();}else{var t=setInterval(function(){if(window.echarts){clearInterval(t);draw();}},100);setTimeout(function(){clearInterval(t);},6000);}})();")
    return (f'<div id="{div}" style="width:100%;max-width:860px;margin:16px auto;height:{max(340,32*len(data))}px;"></div>\n'
            f'<script>\n{js}\n</script>')


def holdings_table(rows, total, n=15):
    body = ""
    for i, r in enumerate(rows[:n], 1):
        body += (f'<tr style="border-bottom:1px solid #eee;"><td>{i}</td><td>{h(r["issuer"])}</td><td>{h(r["cls"])}</td>'
                 f'<td style="text-align:right;">{fmt_money(r["value"])}</td><td style="text-align:right;">{fmt_int(r["shares"])}</td>'
                 f'<td style="text-align:right;">{r["value"]/total*100:.2f}%</td></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;">'
            '<thead><tr style="text-align:left;border-bottom:2px solid #ccc;"><th>#</th><th>公司</th><th>类别</th>'
            '<th style="text-align:right;">市值</th><th style="text-align:right;">股数</th><th style="text-align:right;">权重</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def change_table(rows, kind):
    if not rows:
        return "<p><em>无</em></p>"
    if kind in ("new", "exited"):
        head = '<th>公司</th><th style="text-align:right;">市值</th><th style="text-align:right;">股数</th>'
        body = "".join(f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["issuer"])}</td>'
                       f'<td style="text-align:right;">{fmt_money(r["value"])}</td><td style="text-align:right;">{fmt_int(r["shares"])}</td></tr>'
                       for r in rows[:12])
    else:
        head = '<th>公司</th><th style="text-align:right;">股数变化</th><th style="text-align:right;">变化%</th>'
        body = ""
        for r in rows[:12]:
            sign = "+" if r["dshares"] > 0 else ""
            color = "#c0392b" if r["dshares"] > 0 else "#2e7d32"
            body += (f'<tr style="border-bottom:1px solid #eee;"><td>{h(r["issuer"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{fmt_int(r["dshares"])}</td>'
                     f'<td style="text-align:right;color:{color};">{sign}{r["dpct"]:.1f}%</td></tr>')
    return ('<div style="overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:14px;">'
            f'<thead><tr style="text-align:left;border-bottom:2px solid #ccc;">{head}</tr></thead><tbody>{body}</tbody></table></div>')


def q_label(report):
    y, m, _ = report.split("-")
    return f"{y} Q{(int(m)-1)//3 + 1}"


def build_post(pub_date, quarter, blocks):
    fm = ["---", "layout:     post",
          f'title:      "价值投资 13F 季度追踪：段永平 & 李录 ({quarter})"',
          'subtitle:   "H&H International 与 Himalaya Capital 最新一季美股持仓、重仓与季度增减"',
          f"date:       {pub_date}", 'author:     "龟龟"', 'header-img: "/img/home-bg.jpg"',
          "catalog:    true", "tags:", "    - 投资", "    - 13F", "    - 段永平", "    - 李录", "---", "",
          "> 🤖 **每季自动更新**。数据来自 SEC EDGAR 官方 13F-HR 申报（公开信息，季度报、滞后约 45 天）；"
          "本文为基于公开数据的原创整理，**非投资建议**。", "",
          '<div id="gemini-review" style="border-left:4px solid #4285F4;background:#eef4ff;padding:14px 16px;margin:0 0 22px;border-radius:8px;">',
          '<strong>🔷 Gemini 简评</strong>',
          '<!-- GEMINI_COMMENT_START -->',
          '<p style="color:#999;margin:8px 0 0;">（本篇发布后由 Gemini 自动追加简评）</p>',
          '<!-- GEMINI_COMMENT_END -->',
          '</div>', "", ECHARTS_CDN, ""]
    body = blocks + ["---", "",
                     "*本页依据 SEC EDGAR 公开 13F 申报自动生成，仅供研究记录，不构成任何投资建议。"
                     "13F 仅披露季末美股多头，滞后约 45 天，不含现金/做空/海外持仓。*"]
    return "\n".join(fm + body) + "\n"


def main():
    force = "--force" in sys.argv
    for d in (STATE_DIR, POSTS_DIR, SIDECAR_DIR):
        os.makedirs(d, exist_ok=True)

    data = {}
    for inv in INVESTORS:
        try:
            latest, prev = fetch_13f(inv["cik"])
            if latest:
                data[inv["slug"]] = {"inv": inv, "latest": latest, "prev": prev,
                                     "diff": diff_13f(latest, prev)}
                print(f"[ok] {inv['name']} {latest['report']} holdings={len(latest['holdings'])}")
        except Exception as e:
            print(f"[skip] {inv['name']}: {e}")

    if not data:
        print("NO_DATA")
        return 2

    max_report = max(d["latest"]["report"] for d in data.values())
    last = open(LAST_PATH).read().strip() if os.path.exists(LAST_PATH) else None
    if last == max_report and not force:
        print("NO_NEW_QUARTER")
        return 0

    quarter = q_label(max_report)
    pub_date = max(max(d["latest"]["filed"] for d in data.values()), datetime.date.today().isoformat())
    # filed 日期是公开日；若比今天晚则用今天，避免 future
    pub_date = min(pub_date, datetime.date.today().isoformat())

    blocks, sidecar = [], {"quarter": quarter, "report_date": max_report,
                           "generated_at": datetime.datetime.now().isoformat(timespec="seconds"), "investors": {}}
    for slug, d in data.items():
        inv = d["inv"]; latest = d["latest"]; diff = d["diff"]
        rows = sorted(latest["holdings"].values(), key=lambda r: -r["value"])
        total = sum(r["value"] for r in rows) or 1
        blocks += [f"## {inv['name']}（{inv['entity']}） — {q_label(latest['report'])}", "",
                   f"报告季 **{latest['report']}** ｜ 申报日 {latest['filed']} ｜ {len(rows)} 只持仓 ｜ 组合市值约 {fmt_money(total)}", "",
                   bar_chart(f"tf_{inv['slug']}_bar", rows, total), "",
                   "### 持仓明细（Top 15）", "", holdings_table(rows, total), ""]
        if diff:
            blocks += ["### 季度增减（对比上一季）", "",
                       "**🟥 新建仓**", "", change_table(diff["new"], "new"), "",
                       "**🟩 清仓**", "", change_table(diff["exited"], "exited"), "",
                       "**加仓**", "", change_table(diff["inc"], "inc"), "",
                       "**减仓**", "", change_table(diff["dec"], "dec"), ""]
        else:
            blocks += ["> 暂无上一季数据可对比（首次收录）。", ""]
        sidecar["investors"][slug] = {
            "name": inv["name"], "entity": inv["entity"], "report": latest["report"],
            "total_value": total,
            "holdings": [{"issuer": r["issuer"], "cls": r["cls"], "value": r["value"],
                          "shares": r["shares"], "weight": round(r["value"] / total * 100, 2)} for r in rows],
            "changes": ({k: [{"issuer": x["issuer"], "shares": x.get("dshares", x["shares"]),
                              "value": x["value"]} for x in v] for k, v in diff.items()} if diff else {}),
        }

    md = build_post(pub_date, quarter, blocks)
    out = os.path.join(POSTS_DIR, f"{pub_date}-13f-value-investors.markdown")
    open(out, "w", encoding="utf-8").write(md)
    open(os.path.join(SIDECAR_DIR, f"13f-{max_report}.json"), "w", encoding="utf-8").write(
        json.dumps(sidecar, ensure_ascii=False, indent=2))
    open(LAST_PATH, "w", encoding="utf-8").write(max_report)
    print("POST:" + os.path.relpath(out, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
