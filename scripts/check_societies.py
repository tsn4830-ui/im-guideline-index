#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣醫學會指引監測器
--------------------
定期抓取各學會「指引清單頁」，擷取指引標題＋連結＋年份，與上次結果比對出「新指引」，
輸出 data/societies.json 供前端顯示徽章。純標準庫、無外部相依。

設計原則：
- 只監測「有結構化指引清單、可穩定解析」的學會；JS 動態站不強解析。
- 抓取失敗時「保留上次資料」並標 ok=false，不清空（避免暫時性失聯把畫面清掉）。
- 以標題判斷新舊；第一次執行不標新（全部視為既有）。
"""
import json, os, re, sys, html, datetime, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "societies.json")
UA   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"

# 監測設定：id 對應前端 SOCIETIES 的 id。
# guidelines = 指引清單頁；base = 用來把相對連結補成絕對網址。
SOURCES = [
    {"id": "daroc", "name": "中華民國糖尿病學會",
     "guidelines": "http://www.endo-dm.org.tw/dia/direct/index.asp?t=1",
     "base": "http://www.endo-dm.org.tw/dia/direct/"},
    {"id": "tsn", "name": "台灣腎臟醫學會",
     "guidelines": "https://www.tsn.org.tw/guide.html",
     "base": "https://www.tsn.org.tw/"},
    {"id": "tade", "name": "中華民國糖尿病衛教學會",
     "guidelines": "https://www.tade.org.tw/download/",
     "base": "https://www.tade.org.tw/"},
    {"id": "gest", "name": "台灣消化系醫學會",
     "guidelines": "https://www.gest.org.tw/meeting/",
     "base": "https://www.gest.org.tw/meeting/"},
]

KW   = re.compile(r"指引|共識|照護|建議|準則|規範|年鑑|評估|案例|手冊|專書|診療|治療|standard|guideline|consensus", re.I)
YEAR = re.compile(r"(20[12]\d)")
NOISE = re.compile(r"報名|登入|會員|購物|首頁|上一頁|下一頁|回上|more|回首頁|search|使用說明", re.I)


def clean_title(t):
    t = t.strip("「」『』\"'  　").strip()
    t = re.sub(r"[_\s]*v?\d{0,4}\.pdf$", "", t, flags=re.I)   # 去尾綴 .pdf / _v1203.pdf
    t = re.sub(r"(PDF檔|全文|_FN_?\d*)\s*$", "", t).strip()    # 去尾綴 PDF檔 / 全文 / _FN_
    return t


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    raw = urllib.request.urlopen(req, timeout=25).read()
    # 編碼：優先 meta 宣告，否則 utf-8，再退 big5
    m = re.search(rb'charset=["\']?\s*([\w-]+)', raw[:2000], re.I)
    encs = []
    if m:
        encs.append(m.group(1).decode("ascii", "ignore"))
    encs += ["utf-8", "big5", "cp950"]
    for enc in encs:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def absurl(base, href):
    href = href.strip()
    if href.startswith(("http://", "https://")):
        return href
    if href.startswith("//"):
        return "https:" + href
    return urllib.request.urljoin(base, href)


def extract(source_html, base, fallback):
    """從指引頁擷取 [{title, url, year}]，最新年份優先。
    fallback = 連結若為 javascript/# 等無效值時改用的網址（通常是指引頁本身）。"""
    items, seen = [], set()
    for href, inner in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
                                  source_html, re.S | re.I):
        raw = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        raw = re.sub(r"\s+", " ", raw)
        # 以指引/文件關鍵字判定（含評估、案例、手冊、專書、診療、治療等），
        # 避免把學會期刊會訊等帶年份的非指引項目拉進來。
        if not raw or NOISE.search(raw) or not KW.search(raw):
            continue
        ym = YEAR.search(raw)                 # 年份取自原始標題（含檔名年碼，如 202601）
        title = clean_title(raw)
        if len(title) < 5:
            continue
        key = title[:60]
        if key in seen:
            continue
        seen.add(key)
        url = absurl(base, href)
        if href.strip().lower().startswith(("javascript", "#", "mailto")) or not href.strip():
            url = fallback
        items.append({"title": title[:120], "url": url,
                      "year": int(ym.group(1)) if ym else 0})
    # 年份新→舊；同年維持頁面順序
    items.sort(key=lambda x: -x["year"])
    return items[:6]


def load_prev():
    try:
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def main():
    prev = load_prev()
    prev_soc = prev.get("societies", {})
    today = os.environ.get("TODAY") or datetime.date.today().isoformat()
    out = {"generated": today, "societies": {}}

    for s in SOURCES:
        sid = s["id"]
        prev_items = prev_soc.get(sid, {}).get("items", [])
        prev_titles = {i["title"] for i in prev_items}
        try:
            items = extract(fetch(s["guidelines"]), s["base"], s["guidelines"])
            if not items:
                raise ValueError("no guideline items parsed")
            new_titles = [i["title"] for i in items
                          if prev_titles and i["title"] not in prev_titles]
            out["societies"][sid] = {
                "name": s["name"], "guidelines": s["guidelines"],
                "items": items, "newTitles": new_titles,
                "ok": True, "checked": today,
            }
            print(f"[ok] {sid}: {len(items)} 筆，新 {len(new_titles)} 筆")
        except Exception as e:  # noqa: BLE001
            # 失敗：保留上次資料，標記失敗與檢查時間
            keep = dict(prev_soc.get(sid, {}))
            keep.update({"name": s["name"], "guidelines": s["guidelines"],
                         "ok": False, "checked": today,
                         "newTitles": keep.get("newTitles", [])})
            keep.setdefault("items", prev_items)
            out["societies"][sid] = keep
            print(f"[fail] {sid}: {e}", file=sys.stderr)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"→ 寫入 {OUT}")


if __name__ == "__main__":
    main()
