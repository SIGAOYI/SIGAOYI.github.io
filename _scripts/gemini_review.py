#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 简评（用 Gemini API 生成一段客观简评）。两种用法：

1) 被发帖脚本 import，一次成文：
     import gemini_review as gr
     rev = gr.build_review_html("ark"|"13f", sidecar_dict)   # 无 GEMINI_API_KEY 或失败 -> None
     if rev: md = gr.fill_slot(md, rev)
2) 独立运行做补填：为所有“仍是占位符”的文章补简评（读 ark-data/*.json 再写回）；
   加 --redo 则另把最新一篇 ARK 与最新一篇 13F 的简评重做（覆盖旧简评）。

密钥/模型走环境变量（脚本不含任何密钥）：
  GEMINI_API_KEY   有才会真正调用（放 GitHub Actions Secret）
  GEMINI_MODEL     可选，默认 gemini-2.5-flash

约束：非投资建议；只用给定数据、不编造；不搬第三方正文。
"""
import os, sys, re, json, glob, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
START = "<!-- GEMINI_COMMENT_START -->"
END = "<!-- GEMINI_COMMENT_END -->"
PLACEHOLDER_HINT = "由 Gemini 自动"
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

# 系统提示 = 分类型的格式要求（FMT）+ 通用规则（BASE）。
# 数据里的「值得注意」由脚本确定性算出（signals_*），模型只负责挑重点、说人话，不自己找规律。
FMT = {
    "ark": ("你是财经编辑，给博客读者写本周 ARK 持仓简评。简体中文，两段，段间空一行，"
            "全文 120–200 字（含标点），超出即不合格。时间一律称“本周”。\n"
            "第一段一句话：各基金本周涨跌（带百分比），点出最强与最弱。\n"
            "第二段：从「值得注意」里挑最重要的 1–2 条讲透（带数字，只说数据本身能推出的含义，"
            "如“规模大增主要靠申购而非涨幅”）；再点 2–3 笔最大的买卖，说清是哪只基金。\n"),
    "13f": ("你是财经编辑，给博客读者写本季 13F 持仓简评。简体中文，每位投资人一段，段间空一行，"
            "全文 150–240 字（含标点），超出即不合格。\n"
            "每段先用一句话概括组合（前几大与集中度），再讲本季最大的 2–3 个变化"
            "（新建/清仓/大幅增减持，带数字），优先讲「本季变化」里金额最大的。\n"),
}
BASE = ("称谓：公司一律用中文常见简称（如 特斯拉、苹果、谷歌、拼多多、英伟达、伯克希尔、Coinbase），冷门的直接用股票代码；"
        "基金/机构名也用中文（如 段永平、李录的喜马拉雅资本）。任何名称都不要写英文全称、不要加括号英文（错误示例：谷歌（Alphabet））。\n"
        "禁止：逐只罗列的流水账；空泛套话（如“总体而言”“值得持续关注”“进行了调整”“体现了对……的青睐/信心”）；"
        "猜测动机、市场情绪或数据之外的原因；Markdown 符号（如 **、#、-）。\n"
        "硬性要求：非投资建议，不得出现“建议买入/卖出/加仓/减仓/看多/看空”等指令性措辞；只用给定数据、不编造；"
        "不复制任何第三方文章正文。只输出点评正文，不要标题或解释。")


def fill_slot(md, html):
    """把两个标记之间替换为简评 HTML（保留标记）。"""
    return re.sub(re.escape(START) + r".*?" + re.escape(END),
                  START + "\n" + html + "\n" + END, md, count=1, flags=re.S)


def _money(x):
    a, s = abs(x), ("+" if x > 0 else "-" if x < 0 else "")
    if a >= 1e9:
        return f"{s}${a/1e9:.2f}B"
    if a >= 1e6:
        return f"{s}${a/1e6:.1f}M"
    return f"{s}${a/1e6:.2f}M" if a >= 1e4 else f"{s}${a:,.0f}"


def signals_ark(d):
    """从数据里确定性地挑出“值得注意”的事（按重要性排），交给模型挑 1–2 条讲透。"""
    funds = d.get("funds", {}) or {}
    flows, div, cross, big = [], [], [], []
    for c, f in funds.items():
        prev, ret, flow, pnl = f.get("aum_prev"), f.get("ret_pct"), f.get("flow"), f.get("pnl")
        if prev and ret is not None and flow is not None:
            fp = flow / prev * 100
            way = "流入" if flow > 0 else "流出"
            if abs(fp) >= 1 and ret * flow < 0:      # 涨跌与申赎反向
                flows.append((abs(fp), f"{c} 本周{'涨' if ret > 0 else '跌'} {ret:+.2f}%，资金却净{way} "
                                       f"{_money(flow)}（约占上周规模 {fp:+.1f}%）"))
            elif abs(fp) >= 5:                        # 大额申赎
                tail = "，规模变化主要来自申赎而非涨跌" if pnl is not None and abs(flow) > abs(pnl) else ""
                flows.append((abs(fp), f"{c} 资金大幅净{way} {_money(flow)}（约占上周规模 {fp:+.1f}%）{tail}"))
        wt = f.get("week_trades") or {}
        bought = {x.get("ticker") for x in wt.get("buys", [])}
        sold = {x.get("ticker") for x in wt.get("sells", [])}
        for r in f.get("top") or []:                  # 买卖方向与权重变化相反：价格变动压过了买卖
            dw, lab = r.get("d_week"), r.get("label") or r.get("ticker")
            if dw is None:
                continue
            if r.get("ticker") in sold and dw >= 0.2:
                div.append((dw, f"{c} 卖出 {lab}，但其权重仍升 {dw:+.2f} 个百分点至 {r.get('weight')}%"))
            elif r.get("ticker") in bought and dw <= -0.2:
                div.append((-dw, f"{c} 买入 {lab}，但其权重仍降 {dw:+.2f} 个百分点至 {r.get('weight')}%"))
        for side, act in (("buys", "买入"), ("sells", "卖出")):
            for x in wt.get(side, []):
                big.append((abs(x.get("pct") or 0), f"{c} {act} {x.get('label') or x.get('ticker')}"
                                                     f"（约占净值 {x.get('pct') or 0:+.2f}%）"))
    by_tk = {}                                        # 跨基金：同步买/卖，或此买彼卖
    for c, f in funds.items():
        wt = f.get("week_trades") or {}
        for side in ("buys", "sells"):
            for x in wt.get(side, []):
                by_tk.setdefault(x.get("ticker"), []).append((c, side, x.get("label") or x.get("ticker")))
    for tk, lst in by_tk.items():
        if len(lst) < 2:
            continue
        lab = lst[0][2]
        b = "、".join(c for c, s, _ in lst if s == "buys")
        s = "、".join(c for c, s, _ in lst if s == "sells")
        if b and s:
            cross.append((len(lst), f"{lab} 在 {b} 买入、在 {s} 卖出（基金间此买彼卖）"))
        else:
            cross.append((len(lst), f"{lab} 被 {b or s} 同时{'买入' if b else '卖出'}"))
    out = [t for _, t in sorted(flows, reverse=True)]
    out += [t for _, t in sorted(div, reverse=True)[:2]]
    out += [t for _, t in sorted(cross, reverse=True)[:3]]
    out += ["本周最大一笔：" + t for _, t in sorted(big, reverse=True)[:1]]
    return out


def compact_ark(d):
    lines = [f"# ARK 周报（数据日 {d.get('date')}）"]
    sig = signals_ark(d)
    if sig:
        lines.append("值得注意（脚本按重要性排序）：")
        lines += [f"{i}. {t}" for i, t in enumerate(sig, 1)]
        lines.append("")
    for c, f in d.get("funds", {}).items():
        bits = []
        if f.get("ret_pct") is not None:
            bits.append(f"本周涨跌 {f['ret_pct']:+.2f}%")
        if f.get("pnl") is not None:
            bits.append(f"估算盈亏 {_money(f['pnl'])}")
        if f.get("flow") is not None:
            bits.append(f"估算净申赎 {_money(f['flow'])}")
        if f.get("aum"):
            s = f"规模 {_money(f['aum']).lstrip('+')}"
            if f.get("daum_pct") is not None:
                s += f"（较上周 {f['daum_pct']:+.1f}%）"
            bits.append(s)
        lines.append(f"{c}（{f.get('name')}）" + "；".join(bits))
        top = f.get("top") or [{"label": r.get("ticker"), "weight": r.get("weight")} for r in f.get("holdings", [])[:8]]
        parts = []
        for r in top[:8]:
            s = f"{r.get('label') or r.get('ticker')} {r.get('weight')}%"
            chg = []
            if r.get("d_week") is not None:
                chg.append(f"周{r['d_week']:+.2f}")
            if r.get("d_quarter") is not None:
                chg.append(f"季{r['d_quarter']:+.2f}")
            parts.append(s + ("（" + "、".join(chg) + "）" if chg else ""))
        lines.append("  重仓（权重变化单位：百分点）: " + ", ".join(parts))
        wt = f.get("week_trades")
        if wt:
            b = ", ".join(f"{x.get('label') or x.get('ticker')} +{x.get('pct') or 0:.2f}%" for x in wt.get("buys", [])[:6])
            s = ", ".join(f"{x.get('label') or x.get('ticker')} {x.get('pct') or 0:.2f}%" for x in wt.get("sells", [])[:6])
            lines.append(f"  本周净买入（占净值）: {b or '无'} ｜ 净卖出: {s or '无'}")
    for fund, t in (d.get("week_trades") or {}).items():   # 兼容旧格式（顶层 week_trades、按股数）
        b = ", ".join(f"{x['ticker']}+{x['shares']}" for x in t.get("buys", [])[:6])
        s = ", ".join(f"{x['ticker']}-{x['shares']}" for x in t.get("sells", [])[:6])
        lines.append(f"{fund} 本周买入: {b or '无'} ｜ 卖出: {s or '无'}")
    return "\n".join(lines)


def _cn_name():
    try:                                   # 与 13F 正文同一套中文简称；导入失败就退回原名
        from thirteenf_post import cn_name
        return cn_name
    except Exception:
        return lambda s: (s or "").title()


def _shares_txt(n):
    n = abs(n)
    return f"{n/1e8:.2f} 亿股" if n >= 1e8 else f"{n/1e4:.0f} 万股" if n >= 1e4 else f"{n:,.0f} 股"


def signals_13f(inv, cn):
    """本季变化按金额排序（新建/清仓/增减持统一折成美元），供模型挑重点。"""
    hs, tot = inv.get("holdings", []), inv.get("total_value") or 0
    by_issuer = {}
    for r in hs:
        by_issuer.setdefault(r["issuer"], []).append(r)
    ch, items = inv.get("changes") or {}, []
    for x in ch.get("new", []):
        w = f"，占组合 {x['value']/tot*100:.1f}%" if tot else ""
        items.append((x["value"], f"新建 {cn(x['issuer'])}，约 {_money(x['value']).lstrip('+')}{w}"))
    for x in ch.get("exited", []):
        items.append((x["value"], f"清仓 {cn(x['issuer'])}（上季约 {_money(x['value']).lstrip('+')}）"))
    for k, act in (("inc", "增持"), ("dec", "减持")):
        for x in ch.get(k, []):
            ds, amt, pct = x.get("shares") or 0, None, x.get("dpct")
            m = by_issuer.get(x["issuer"], [])
            if len(m) == 1 and m[0].get("shares"):          # 同名多类股时无法对应，只报股数
                cur = m[0]["shares"]
                amt = ds * m[0]["value"] / cur
                if pct is None and cur - ds > 0:
                    pct = ds / (cur - ds) * 100
            s = f"{act} {cn(x['issuer'])} {_shares_txt(ds)}"
            if pct is not None:
                s += f"（股数 {pct:+.0f}%）"
            if amt is not None:
                s += f"，约 {_money(amt)}"
            items.append((abs(amt) if amt is not None else 0, s))
    return [t for _, t in sorted(items, key=lambda z: -z[0])[:5]]


def compact_13f(d):
    cn = _cn_name()
    lines = [f"# 13F 季报（{d.get('quarter')}，报告季 {d.get('report_date')}）"]
    for slug, inv in d.get("investors", {}).items():
        agg = {}                                            # 同一公司多类股（如谷歌 A/C）合并
        for r in inv.get("holdings", []):
            n = cn(r["issuer"])
            agg[n] = agg.get(n, 0) + (r.get("weight") or 0)
        top = sorted(agg.items(), key=lambda kv: -kv[1])
        tot = _money(inv.get("total_value") or 0).lstrip("+")
        # 只给中文人名，不给英文机构名，免得被写进正文
        lines.append(f"{inv.get('name')}：{len(agg)} 家公司，组合约 {tot}，前三大合计 {sum(w for _, w in top[:3]):.1f}%")
        lines.append("  重仓: " + ", ".join(f"{n} {w:.1f}%" for n, w in top[:10]))
        sig = signals_13f(inv, cn)
        if sig:
            lines.append("  本季变化（按金额排序）: " + "；".join(sig))
        elif not inv.get("changes"):
            lines.append("  （无上一季可对比）")
    return "\n".join(lines)


def call_gemini(prompt, sys_text):
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": sys_text}]},
        "contents": [{"parts": [{"text": prompt}]}],
        # thinkingBudget:0 尝试关闭思考；有时不生效，故 maxOutputTokens 放大到 2048 兜底防截断
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048,
                             "thinkingConfig": {"thinkingBudget": 0}},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    cand = resp["candidates"][0]
    fin = cand.get("finishReason")
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", [])).strip()
    u = resp.get("usageMetadata", {})
    print(f"[usage] model={MODEL} prompt_tokens={u.get('promptTokenCount')} "
          f"output_tokens={u.get('candidatesTokenCount')} thoughts_tokens={u.get('thoughtsTokenCount')} "
          f"total={u.get('totalTokenCount')} finish={fin}")
    return text


def build_review_html(kind, sidecar):
    """无 key 或失败/过短 -> None；否则返回可直接嵌入 slot 的 HTML。发帖脚本据此一次成文。"""
    if not os.environ.get("GEMINI_API_KEY"):
        print("[gemini-skip] 无 GEMINI_API_KEY，保留占位符")
        return None
    try:
        data_txt = compact_ark(sidecar) if kind == "ark" else compact_13f(sidecar)
        review = call_gemini(data_txt + "\n\n请据此写简评。", FMT[kind] + BASE)
    except Exception as e:
        print("[gemini-skip]", e)
        return None
    if len(review) < 40:
        print(f"[gemini-skip] 简评过短（{len(review)} 字），保留占位符")
        return None
    print(f"[gemini] 简评 {len(review)} 字")
    return (review_to_html(review) + "\n"
            f'<p style="color:#888;font-size:12px;">🔷 由 Gemini（{MODEL}）自动生成，非投资建议。</p>')


def review_to_html(text):
    """模型输出 -> 每段一个 <p>：去 Markdown 符号、转义 HTML、拆开 Liquid 定界符（Jekyll 会解析 {{ {%）。"""
    t = text.replace("**", "").replace("__", "")
    t = re.sub(r"^\s*(?:#+|>|\*|•|-(?=\s))\s*", "", t, flags=re.M)
    t = t.replace("{{", "{ {").replace("{%", "{ %")
    paras = [p.strip() for p in t.splitlines() if p.strip()]
    return "\n".join(f"<p>{html.escape(p, quote=False)}</p>" for p in paras)


# ---- 独立运行：为所有“待填”文章补简评（备用/补填，一次跑填全部） ----
def _find_all_pending(redo=False):
    """待填 = slot 里仍是占位符；redo=True 时另把最新一篇 ARK 和最新一篇 13F 也算上（覆盖旧简评）。"""
    out, seen = [], set()
    cands = sorted(glob.glob(os.path.join(POSTS_DIR, "*-ark-cathie-wood.markdown")) +
                   glob.glob(os.path.join(POSTS_DIR, "*-13f-value-investors.markdown")), reverse=True)
    for p in cands:
        kind = "ark" if "ark-cathie-wood" in os.path.basename(p) else "13f"
        newest = kind not in seen          # 文件名以日期开头、倒序，同类第一个即最新
        seen.add(kind)
        s = open(p, encoding="utf-8").read()
        m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), s, re.S)
        if not (m and (PLACEHOLDER_HINT in m.group(1) or (redo and newest))):
            continue
        if kind == "ark":
            dm = re.search(r"数据日期：(\d{4}-\d{2}-\d{2})", s)
            out.append((p, "ark", os.path.join(SIDECAR_DIR, f"{dm.group(1)}.json") if dm else None))
        else:
            rm = re.search(r"报告季 \*\*(\d{4}-\d{2}-\d{2})\*\*", s)
            out.append((p, "13f", os.path.join(SIDECAR_DIR, f"13f-{rm.group(1)}.json") if rm else None))
    return out


def main():
    pend = _find_all_pending(redo="--redo" in sys.argv)
    if not pend:
        print("NO_PENDING_POST")
        return 0
    filled = 0
    for path, kind, sidecar_path in pend:
        if not sidecar_path or not os.path.exists(sidecar_path):
            print("NO_SIDECAR:", path)
            continue
        rev = build_review_html(kind, json.load(open(sidecar_path, encoding="utf-8")))
        if not rev:
            continue  # 无 key / 失败：保留占位符
        s = open(path, encoding="utf-8").read()          # 必须先读，再以 "w" 打开写，否则会先清空文件
        open(path, "w", encoding="utf-8").write(fill_slot(s, rev))
        print("FILLED:" + os.path.relpath(path, ROOT))
        filled += 1
    print(f"filled={filled}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
