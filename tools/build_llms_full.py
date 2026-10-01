#!/usr/bin/env python3
"""llms-full.txt: the English text of every growth page in one plain file, for LLMs (2026-09-30, Ron).

llms.txt stays the curated map; this file carries the full answers behind it: for every page in
content/pages/*.json (advisory, local and area pages, partner pages, guides, projects), the title, the
URL, the lead, the body as plain text and the questions with their answers. English only (the Hebrew
twin is on the same URL). Written by build.py after the pages; never edit llms-full.txt by hand.
"""
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://stavtheodor.com"
ORDER = ["local", "area", "advisory", "partners", "guide", "projects"]
HEAD = {"local": "Local pages", "area": "Town and county pages", "advisory": "Advisory pages",
        "partners": "For partners", "guide": "Guides", "projects": "Projects"}


def text(h):
    h = re.sub(r"<(figure|aside)\b[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<li[^>]*>", "\n- ", h)
    h = re.sub(r"<h[23][^>]*>", "\n\n### ", h)
    h = re.sub(r"</(p|h2|h3|ul|ol)>", "\n", h)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", h)).strip()


def main():
    pages = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(ROOT, "content/pages/*.json")))]
    out = ["# THEODORA Art Advisory by Stav Theodor: full text of the advisory pages and guides", "",
           "> The English text of every advisory, local, partner, guide and project page on stavtheodor.com, "
           "in one plain file. The curated map is https://stavtheodor.com/llms.txt; short answers are in "
           "https://stavtheodor.com/answers.md. Each page is bilingual (English and Hebrew) at the URL given. "
           "THEODORA Art Advisory by Stav Theodor is based in Tenafly, New Jersey, and is not affiliated with "
           "Theadora Art Advisory (Los Angeles) or TSG Art Advisory. Contact: stav@stavtheodor.com, (201) 351-8367.", ""]
    for sec in ORDER:
        group = [p for p in pages if p.get("section") == sec]
        if not group:
            continue
        group.sort(key=lambda p: p["path"])
        out += [f"## {HEAD[sec]}", ""]
        for p in group:
            out += [f"### {p['title_en']}", "", f"URL: {SITE}/{p['path'].strip('/')}/", "", p.get("lead_en", ""), "",
                    text(p.get("body_en", "")), ""]
            faq = p.get("faq") or []
            if faq:
                out += ["Questions:", ""]
                for q in faq:
                    out += [f"Q: {q['q_en']}", f"A: {text(q['a_en'])}", ""]
    body = "\n".join(out).rstrip() + "\n"
    if re.search("[\u2013\u2014]", body):
        raise SystemExit("llms-full.txt: an em or en dash reached the text; fix the page source")
    open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8").write(body)
    print(f"llms-full.txt: {sum(1 for p in pages if p.get('section') in ORDER)} pages, {len(body.split())} words")


if __name__ == "__main__":
    main()
