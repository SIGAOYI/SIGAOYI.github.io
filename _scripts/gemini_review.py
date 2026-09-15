#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 Gemini API 为最新一篇自动持仓文（ARK 周报 / 13F 季报）追加「Gemini 简评」，填进正文顶部的置顶栏。

- 找 _posts/ 里最新一篇“标记之间仍是占位符”的 ark-cathie-wood 或 13f-value-investors 文章。
- 读对应 ark-data/*.json，**裁剪**成紧凑摘要（控制 token），拼进提示词。
- 调 Gemini generateContent，取简评，替换两个标记之间的内容（其余不动）。
- 打印 usageMetadata（真实 token 用量）。提交/推送由工作流完成。

密钥/模型从环境变量读，脚本本身不含任何密钥：
  GEMINI_API_KEY   必填（放 GitHub Actions Secret）
  GEMINI_MODEL     可选，默认 gemini-2.5-flash

用法：
  python3 _scripts/gemini_review.py            # 真正调用 API（需 GEMINI_API_KEY）
  python3 _scripts/gemini_review.py --dry-run  # 不调用、不花钱：只打印将发送的字符数与粗略 token 估算
退出码：0 正常（含无待填文章跳过）；2 出错。
"""
import os, sys, re, json, glob, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "_posts")
SIDECAR_DIR = os.path.join(ROOT, "ark-data")
START = "<!-- GEMINI_COMMENT_START -->"
END = "<!-- GEMINI_COMMENT_END -->"
PLACEHOLDER_HINT = "由 Gemini 自动"
MODEL = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"

SYS = ("你是金融数据编辑。基于给定的结构化数据，用简体中文写一段 120–220 字的客观简评。"
       "硬性要求：非投资建议，不得出现“建议买入/卖出/加仓/减仓/看多/看空”等指令性措辞；"
       "只用给定数据、不编造数字；不复制任何第三方文章正文。只输出简评正文本身，不要额外解释。")


def find_target():
    """返回 (post_path, kind, date_or_report)；kind in {'ark','13f'}。无则 None。"""
    cands = sorted(glob.glob(os.path.join(POSTS_DIR, "*-ark-cathie-wood.markdown")) +
                   glob.glob(os.path.join(POSTS_DIR, "*-13f-value-investors.markdown")), reverse=True)
    for p in cands:
        s = open(p, encoding="utf-8").read()
        m = re.search(re.escape(START) + r"(.*?)" + re.escape(END), s, re.S)
        if m and PLACEHOLDER_HINT in m.group(1):
            base = os.path.basename(p)
            if "ark-cathie-wood" in base:
                # 数据日期在正文“数据日期：YYYY-MM-DD”
                dm = re.search(r"数据日期：(\d{4}-\d{2}-\d{2})", s)
                return p, "ark", (dm.group(1) if dm else base[:10])
            else:
                rm = re.search(r"报告季 \*\*(\d{4}-\d{2}-\d{2})\*\*", s)
                return p, "13f", (rm.group(1) if rm else None)
    return None


def compact_ark(date):
    d = json.load(open(os.path.join(SIDECAR_DIR, f"{date}.json"), encoding="utf-8"))
    lines = [f"# ARK 周报数据（截至 {d.get('date')}）"]
    for c, f in d.get("funds", {}).items():
        top = ", ".join(f"{r['ticker']} {r['weight']}%" for r in f["holdings"][:8])
        lines.append(f"{c}（{f['name']}）Top: {top}")
    for fund, t in d.get("week_trades", {}).items():
        b = ", ".join(f"{x['ticker']}+{x['shares']}" for x in t.get("buys", [])[:6])
        s = ", ".join(f"{x['ticker']}-{x['shares']}" for x in t.get("sells", [])[:6])
        lines.append(f"{fund} 本周买入: {b or '无'} ｜ 卖出: {s or '无'}")
    return "\n".join(lines)


def compact_13f(report):
    d = json.load(open(os.path.join(SIDECAR_DIR, f"13f-{report}.json"), encoding="utf-8"))
    lines = [f"# 13F 季报数据（报告季 {report}，{d.get('quarter')}）"]
    for slug, inv in d.get("investors", {}).items():
        top = ", ".join(f"{r['issuer']} {r['weight']}%" for r in inv["holdings"][:10])
        lines.append(f"{inv['name']}（{inv['entity']}）重仓: {top}")
        ch = inv.get("changes", {})
        if ch:
            nb = ", ".join(x["issuer"] for x in ch.get("new", [])[:5])
            ex = ", ".join(x["issuer"] for x in ch.get("exited", [])[:5])
            lines.append(f"  新建: {nb or '无'} ｜ 清仓: {ex or '无'}")
    return "\n".join(lines)


def call_gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("ERROR: 未设置 GEMINI_API_KEY 环境变量（应放 GitHub Actions Secret）")
        sys.exit(2)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={key}"
    body = json.dumps({
        "system_instruction": {"parts": [{"text": SYS}]},
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 500},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
    u = resp.get("usageMetadata", {})
    print(f"[usage] model={MODEL} prompt_tokens={u.get('promptTokenCount')} "
          f"output_tokens={u.get('candidatesTokenCount')} total={u.get('totalTokenCount')}")
    return text


def main():
    dry = "--dry-run" in sys.argv
    t = find_target()
    if not t:
        print("NO_PENDING_POST")
        return 0
    path, kind, ref = t
    data_txt = compact_ark(ref) if kind == "ark" else compact_13f(ref)
    prompt = data_txt + "\n\n请据此写简评。"
    print(f"[target] {os.path.basename(path)} kind={kind} ref={ref}")

    if dry:
        chars = len(SYS) + len(prompt)
        print(f"[dry-run] 将发送字符数≈{chars}（系统+数据+指令）；粗略 token 估算 ≈ {int(chars/3)}–{int(chars/2)}。"
              f" 未调用 API、未花费。设 GEMINI_API_KEY 后去掉 --dry-run 即测真实用量。")
        return 0

    review = call_gemini(prompt)
    html = (f"<p>{review}</p>\n"
            f'<p style="color:#888;font-size:12px;">🔷 由 Gemini（{MODEL}）自动生成，非投资建议。</p>')
    s = open(path, encoding="utf-8").read()
    s2 = re.sub(re.escape(START) + r".*?" + re.escape(END),
                START + "\n" + html + "\n" + END, s, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(s2)
    print("FILLED:" + os.path.relpath(path, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
