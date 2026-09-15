#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 简评（用 Gemini API 生成一段客观简评）。两种用法：

1) 被发帖脚本 import，一次成文：
     import gemini_review as gr
     rev = gr.build_review_html("ark"|"13f", sidecar_dict)   # 无 GEMINI_API_KEY 或失败 -> None
     if rev: md = gr.fill_slot(md, rev)
2) 独立运行做补填：为最新一篇“仍是占位符”的文章补简评（读 ark-data/*.json 再写回）。

密钥/模型走环境变量（脚本不含任何密钥）：
  GEMINI_API_KEY   有才会真正调用（放 GitHub Actions Secret）
  GEMINI_MODEL     可选，默认 gemini-2.5-flash

约束：非投资建议；只用给定数据、不编造；不搬第三方正文。
"""
import os, sys, re, json, glob, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
START = "<!-- GEMINI_COMMENT_START -->"
END = "<!-- GEMINI_COMMENT_END -->"
PLACEHOLDER_HINT = "由 Gemini 自动"
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

SYS = ("你是金融数据编辑。基于给定的结构化数据，用简体中文写一段 150–250 字的客观简评。"
       "硬性要求：非投资建议，不得出现“建议买入/卖出/加仓/减仓/看多/看空”等指令性或劝诱性措辞；"
       "只用给定数据、不编造数字；不复制任何第三方文章正文。只输出简评正文本身，不要额外解释或标题。")


def fill_slot(md, html):
    """把两个标记之间替换为简评 HTML（保留标记）。"""
    return re.sub(re.escape(START) + r".*?" + re.escape(END),
                  START + "\n" + html + "\n" + END, md, count=1, flags=re.S)


def compact_ark(d):
    lines = [f"# ARK 周报（截至 {d.get('date')}）"]
    for c, f in d.get("funds", {}).items():
        top = ", ".join(f"{r['ticker']} {r['weight']}%" for r in f.get("holdings", [])[:8])
        lines.append(f"{c}（{f.get('name')}）Top: {top}")
    for fund, t in d.get("week_trades", {}).items():
        b = ", ".join(f"{x['ticker']}+{x['shares']}" for x in t.get("buys", [])[:6])
        s = ", ".join(f"{x['ticker']}-{x['shares']}" for x in t.get("sells", [])[:6])
        lines.append(f"{fund} 本周买入: {b or '无'} ｜ 卖出: {s or '无'}")
    return "\n".join(lines)


def compact_13f(d):
    lines = [f"# 13F 季报（{d.get('quarter')}，报告季 {d.get('report_date')}）"]
    for slug, inv in d.get("investors", {}).items():
        top = ", ".join(f"{r['issuer']} {r['weight']}%" for r in inv.get("holdings", [])[:10])
        lines.append(f"{inv.get('name')}（{inv.get('entity')}）重仓: {top}")
        ch = inv.get("changes", {})
        if ch:
            nb = ", ".join(x["issuer"] for x in ch.get("new", [])[:5])
            ex = ", ".join(x["issuer"] for x in ch.get("exited", [])[:5])
            lines.append(f"  新建: {nb or '无'} ｜ 清仓: {ex or '无'}")
    return "\n".join(lines)


def call_gemini(prompt):
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYS}]},
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
        review = call_gemini(data_txt + "\n\n请据此写简评。")
    except Exception as e:
        print("[gemini-skip]", e)
        return None
    if len(review) < 40:
        print(f"[gemini-skip] 简评过短（{len(review)} 字），保留占位符")
        return None
    return (f"<p>{review}</p>\n"
            f'<p style="color:#888;font-size:12px;">🔷 由 Gemini（{MODEL}）自动生成，非投资建议。</p>')


# ---- 独立运行：为最新一篇“待填”文章补简评（备用/补填） ----
def _find_pending():
    cands = sorted(glob.glob(os.path.join(POSTS_DIR, "*-ark-cathie-wood.markdown")) +
                   glob.glob(os.path.join(POSTS_DIR, "*-13f-value-investors.markdown")), reverse=True)
    for p in cands:
        s = open(p, encoding="utf-8").read()
        m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), s, re.S)
        if m and PLACEHOLDER_HINT in m.group(1):
            if "ark-cathie-wood" in os.path.basename(p):
                dm = re.search(r"数据日期：(\d{4}-\d{2}-\d{2})", s)
                return p, "ark", (os.path.join(SIDECAR_DIR, f"{dm.group(1)}.json") if dm else None)
            rm = re.search(r"报告季 \*\*(\d{4}-\d{2}-\d{2})\*\*", s)
            return p, "13f", (os.path.join(SIDECAR_DIR, f"13f-{rm.group(1)}.json") if rm else None)
    return None


def main():
    t = _find_pending()
    if not t:
        print("NO_PENDING_POST")
        return 0
    path, kind, sidecar_path = t
    if not sidecar_path or not os.path.exists(sidecar_path):
        print("NO_SIDECAR:", sidecar_path)
        return 0
    rev = build_review_html(kind, json.load(open(sidecar_path, encoding="utf-8")))
    if not rev:
        return 2
    open(path, "w", encoding="utf-8").write(fill_slot(open(path, encoding="utf-8").read(), rev))
    print("FILLED:" + os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
