#!/usr/bin/env python3
"""Mechanical gate for content/pages/*.json. Prints OK or the list of failures. Exit 1 on any failure."""
import json, re, sys, os
ALLOWED = {"p","h2","h3","ul","ol","li","strong","em","a","blockquote","figure","img","figcaption","br"}
LIMITS = {"advisory": (500, 900), "projects": (250, 450), "partners": (400, 700), "guide": (900, 1400)}
HYPE = ["elevate", "curated experience", "bespoke journey", "unparalleled", "world-class", "world class", "transform your", "seamlessly", "elevating"]
def words(s): return len(re.sub(r"<[^>]+>", " ", s).split())
fails_total = 0
for f in sys.argv[1:]:
    fails = []
    try: p = json.load(open(f, encoding="utf-8"))
    except Exception as e: print(f"{f}: FAIL invalid JSON: {e}"); fails_total += 1; continue
    raw = json.dumps(p, ensure_ascii=False)
    if re.search(r"[—–]", raw): fails.append("em/en dash present")
    if re.search(r"\b\d{3}[ .-]\d{3}[ .-]\d{4}\b|\+1[ (]|\b0\d{2}[ -]?\d{7}\b|\+972", raw): fails.append("phone number present")
    for k in ["path","section","title_en","title_he","meta_description","lead_en","lead_he","body_en","body_he"]:
        if not p.get(k): fails.append(f"missing {k}")
    if p.get("section") not in LIMITS: fails.append("bad section")
    if len(p.get("meta_description","")) > 165: fails.append("meta_description over 165 chars")
    if p.get("section") == "projects" and not p.get("hero_image"): fails.append("project page without hero_image")
    for blk in ["body_en","body_he"]:
        tags = set(t.lower() for t in re.findall(r"<\s*([a-zA-Z0-9]+)", p.get(blk,"")))
        bad = tags - ALLOWED
        if bad: fails.append(f"{blk} disallowed tags: {sorted(bad)}")
        for m in re.finditer(r"<img[^>]*>", p.get(blk,"")):
            if 'alt="' not in m.group(0) or 'alt=""' in m.group(0): fails.append(f"{blk} img without alt")
            src = re.search(r'src="([^"]+)"', m.group(0))
            if src and not os.path.exists(src.group(1).lstrip("/")): fails.append(f"{blk} missing image {src.group(1)}")
        if re.search(r'style=|class=|<script', p.get(blk,"")): fails.append(f"{blk} has style/class/script")
    if p.get("section") in LIMITS and p.get("body_en"):
        lo, hi = LIMITS[p["section"]]; n = words(p["body_en"])
        if n < lo or n > hi: fails.append(f"body_en {n} words, expected {lo} to {hi}")
    if p.get("body_he") and words(p["body_he"]) < 0.6 * words(p.get("body_en","")): fails.append("body_he much shorter than body_en, translation incomplete")
    low = p.get("body_en","").lower()
    for h in HYPE:
        if h in low: fails.append(f"hype word: {h}")
    if re.search(r"\$\s?\d|\d+\s?%", p.get("body_en","")) and "industry" not in low: fails.append("numbers with $ or % but no 'industry' labeling")
    for q in p.get("faq", []) or []:
        for k in ["q_en","a_en","q_he","a_he"]:
            if not q.get(k): fails.append(f"faq item missing {k}")
        n = words(q.get("a_en","")); 
        if n and (n < 30 or n > 110): fails.append(f"faq answer {n} words, expected 40 to 90")
    if p.get("hero_image") and not os.path.exists(p["hero_image"]["src"].lstrip("/")): fails.append("hero_image file missing")
    if len(p.get("related", [])) < 2 and p.get("section") != "guide": fails.append("fewer than 2 related pages")
    if fails: print(f"{f}: FAIL\n  - " + "\n  - ".join(fails)); fails_total += 1
    else: print(f"{f}: OK ({words(p['body_en'])} en words)")
sys.exit(1 if fails_total else 0)
