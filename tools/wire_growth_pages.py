#!/usr/bin/env python3
"""Idempotent: adds nav links and an Advisory section to index.html, lists the growth
pages in llms.txt and agent.txt, appends four answers to answers.md. Reads titles and
descriptions from content/pages/*.json. Run from repo root after build-site-pages.py."""
import glob, json, re, html as H
SITE = "https://stavtheodor.com"
pages = [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob("content/pages/*.json"))]
by = {p["path"].strip("/"): p for p in pages}
adv = [p for p in pages if p["section"] == "advisory"]
prj = [p for p in pages if p["section"] == "projects"]
def t(path): return by[path]["title_en"] if path in by else None

# ---- index.html ----
s = open("index.html", encoding="utf-8", newline="").read()
if 'href="/advisory/"' not in s:
    s = s.replace('  <a href="#portfolio">Portfolio</a>\n', '  <a href="#portfolio">Portfolio</a>\n  <a href="/advisory/">Advisory</a>\n  <a href="/projects/">Projects</a>\n', 1)
if 'id="advisory-links"' not in s:
    links = [("/advisory/", "Art advisory, answered plainly: what it costs, how it works, where I work"),
             ("/projects/", "Projects: homes in Manhattan, New Jersey, Tel Aviv and Caesarea, hotels, one exhibition in Geneva")]
    for path in ["for-designers", "for-brokers", "for-advisors", "guide/ten-questions-before-you-buy-your-first-serious-artwork"]:
        if path in by: links.append((f"/{path}/", by[path]["title_en"]))
    li = "\n".join(f'    <li><a href="{h}">{H.escape(txt)}</a></li>' for h, txt in links)
    block = f'''<!-- ============ ADVISORY LINKS (generated 2026-09-06 by tools/wire_growth_pages.py) ============ -->
<section id="advisory-links" class="wrap">
  <div class="label">Advisory</div>
  <p class="portfolio-lead">If you are about to buy, build or move, start here. These pages answer the questions I am asked most, in plain terms, and show the work behind the answers.</p>
  <ul style="list-style:none; padding:0; margin:18px 0 0; line-height:2;">
{li}
  </ul>
</section>

<hr class="divider">

'''
    m = re.search(r'<section id="about" class="wrap">.*?</section>\s*\n\s*<hr class="divider">\s*\n', s, re.S)
    assert m, "about section not found"
    s = s[:m.end()] + "\n" + block + s[m.end():]
open("index.html", "w", encoding="utf-8", newline="").write(s)

# ---- llms.txt ----
s = open("llms.txt", encoding="utf-8").read()
s = re.sub(r"\n## Advisory pages\n.*?(?=\n## |\Z)", "", s, flags=re.S)
s = re.sub(r"\n## Project pages\n.*?(?=\n## |\Z)", "", s, flags=re.S)
adv_lines = "\n".join(f"- [{p['title_en']}]({SITE}/{p['path'].strip('/')}/): {p['meta_description']}" for p in adv)
extra = [p for p in pages if p["section"] in ("partners", "guide")]
adv_lines += "\n" + "\n".join(f"- [{p['title_en']}]({SITE}/{p['path'].strip('/')}/): {p['meta_description']}" for p in extra)
prj_lines = "\n".join(f"- [{p['title_en']}]({SITE}/{p['path'].strip('/')}/): {p['meta_description']}" for p in prj)
block = f"\n## Advisory pages\n\nPlain answers for people about to buy, build or move, each in English and Hebrew on the same page. Hub: {SITE}/advisory/\n\n{adv_lines}\n\n## Project pages\n\nCase studies of completed work, each with photographs. Hub: {SITE}/projects/\n\n{prj_lines}\n"
anchor = "\n## Founder"
assert anchor in s
s = s.replace(anchor, block + anchor, 1)
open("llms.txt", "w", encoding="utf-8").write(s)

# ---- agent.txt ----
s = open("agent.txt", encoding="utf-8").read()
if "## Advisory and project pages" not in s:
    s = s.rstrip("\n") + f"""

## Advisory and project pages

Since September 2026 the site also carries advisory pages ({SITE}/advisory/) that answer hiring questions
(what an art advisor costs, how the process works, art for a new build in Bergen County, art for a home in
Israel managed from abroad, commissions, collections, offices, hotels) and project case studies
({SITE}/projects/). Partner pages: {SITE}/for-designers/, {SITE}/for-brokers/, {SITE}/for-advisors/.
Guide: {SITE}/guide/ten-questions-before-you-buy-your-first-serious-artwork/. Every one of these pages is
bilingual, Hebrew and English in the same HTML, with FAQPage structured data in English.
Contact for advisory enquiries: Stav@stavtheodor.com
"""
    open("agent.txt", "w", encoding="utf-8").write(s)

# ---- answers.md ----
s = open("answers.md", encoding="utf-8").read()
if "## What does an art advisor cost?" not in s:
    def ans(path, q):
        p = by.get(path)
        if not p: return ""
        lead = re.sub(r"<[^>]+>", "", p["lead_en"]).strip()
        return f"\n## {q}\n\n{lead} Full page, in English and Hebrew: {SITE}/{path}/\n"
    add = ans("advisory/what-does-an-art-advisor-cost", "What does an art advisor cost?") + \
          ans("advisory/how-the-art-advisory-process-works", "How does working with an art advisor work, step by step?") + \
          ans("advisory/art-for-a-new-build-in-bergen-county", "When should art come into a new house in Alpine, Tenafly or Closter, New Jersey?") + \
          ans("advisory/commissioning-art-for-a-new-home", "How do I commission an artwork made for my home?") + \
          ans("advisory/art-for-a-home-in-israel-from-abroad", "Can an art advisor in New York handle a home in Caesarea or Tel Aviv?")
    s = s.rstrip("\n") + "\n" + add
    open("answers.md", "w", encoding="utf-8").write(s)
print("wired:", len(adv), "advisory,", len(prj), "projects,", len(extra), "partner/guide")
