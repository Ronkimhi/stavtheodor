#!/usr/bin/env python3
"""llms-full.txt: the English text of every growth page, then every Art Radar post, in one plain file, for LLMs.

llms.txt stays the curated map; this file carries the full text behind it.
Growth pages (2026-09-30, Ron): for every page in content/pages/*.json (advisory, local and area pages, partner pages,
guides, projects), the title, the URL, the lead, the body as plain text and the questions with their answers.
Art Radar posts (Ron, 2026-11-20, ron-decisions row 23): for every post in content/posts.html, newest first, its
English title, its datePublished, its canonical /radar/<slug>/ URL and the English text of the post verbatim, read
from the post's English body block: every paragraph, line break and figure caption as Stav published it, with tags
removed and nothing summarized, reworded or dropped (auction figures included, as written). Images, video and the
image alt text are not text of the post and are left out. A new post appears here on the next build, no manual step.
English only (the Hebrew twin is on the same URL). Written by build.py after the pages; never edit llms-full.txt by
hand.
"""
import glob
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import site_chrome as sc  # noqa: E402

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


def post_text(h):
    """A post's English body block as plain text, verbatim: each paragraph, caption and venue line on its own line
    (a <br> is a line break), tags removed, entities decoded, runs of spaces folded. No word is added or dropped."""
    h = re.sub(r"<(video|iframe|audio)\b[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<(img|source)\b[^>]*>", " ", h, flags=re.I)
    h = re.sub(r"<br\s*/?>", "\n", h, flags=re.I)
    h = re.sub(r"<li[^>]*>", "\n- ", h, flags=re.I)
    h = re.sub(r"</(p|div|figure|figcaption|h[1-6]|ul|ol|li|blockquote)>", "\n\n", h, flags=re.I)
    h = html.unescape(re.sub(r"<[^>]+>", "", h))
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in h.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def radar_section():
    """The Art Radar part: every post in content/posts.html, newest first (file order)."""
    _, posts = sc.read_posts(os.path.join(ROOT, "content", "posts.html"))
    out = ["## Art Radar posts", "",
           "Stav Theodor's own posts on current exhibitions, museums and the art market in New York, New Jersey and "
           "Tel Aviv, newest first. Each is the English text of the post as published (the Hebrew original is on the "
           "same URL). The archive is https://stavtheodor.com/radar/.", ""]
    for p in posts:
        body = post_text(sc.post_body(p["article_inner"], "en"))
        if not body:
            raise SystemExit(f"llms-full.txt: post {p['slug']} has no English body block")
        out += [f"### {p['title_en']}", "", f"Published: {p['datePublished']}",
                f"URL: {SITE}/radar/{p['slug']}/", "", body, ""]
    return out, len(posts)


def main():
    pages = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(os.path.join(ROOT, "content/pages/*.json")))]
    out = ["# THEODORA Art Advisory by Stav Theodor: full text of the advisory pages, guides and Art Radar posts", "",
           "> The English text of every advisory, local, partner, guide and project page on stavtheodor.com, "
           "and of every Art Radar post, in one plain file. The curated map is https://stavtheodor.com/llms.txt; short "
           "answers are in https://stavtheodor.com/answers.md. Each page and post is bilingual (English and Hebrew) at "
           "the URL given. THEODORA Art Advisory by Stav Theodor is based in Tenafly, New Jersey, and is not affiliated "
           "with Theadora Art Advisory (Los Angeles) or TSG Art Advisory. Contact: stav@stavtheodor.com, (201) 351-8367.", ""]
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
    radar, n_posts = radar_section()
    out += radar
    body = "\n".join(out).rstrip() + "\n"
    if re.search("[\u2013\u2014]", body):
        raise SystemExit("llms-full.txt: an em or en dash reached the text; fix the page or post source")
    open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8").write(body)
    print(f"llms-full.txt: {sum(1 for p in pages if p.get('section') in ORDER)} pages, {n_posts} Art Radar posts, "
          f"{len(body.split())} words")


if __name__ == "__main__":
    main()
