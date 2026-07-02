#!/usr/bin/env python3
"""
build_artist_pages.py — generates static, crawlable HTML for The Museum:

  museum/artists/index.html          the collection directory (20 periods, all artists)
  museum/artists/<slug>/index.html   one placard-style page per artist

These are the indexable, LLM-readable faces of the interactive museum
(the timeline and 3D galleries are JS apps that crawlers can't walk).
All text comes verbatim from museum/data/*.json, which the fetch pipeline
sources from Wikipedia/Wikidata/Commons. Re-run after refreshing the data:

    python3 museum/tools/build_artist_pages.py
"""

import html
import json
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
MUSEUM = HERE.parent
DATA = MUSEUM / "data"
OUT = MUSEUM / "artists"
SITE = "https://stavtheodor.com"

GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4300MN0Q97"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-4300MN0Q97');
</script>"""

THEME_SNIPPET = """<script>
(function () {
  try {
    var t = localStorage.getItem('museumTheme') || 'light';
    document.documentElement.dataset.theme = t;
  } catch (e) {}
})();
</script>"""

PAGE_CSS = """<style>
  body { max-width: 760px; margin: 0 auto; padding: 92px 24px 80px; }
  .crumb { font-size: 12.5px; letter-spacing: 0.18em; text-transform: uppercase; }
  .crumb a { text-decoration: none; color: var(--ink-soft); }
  .crumb a:hover { color: var(--bronze); }
  h1 { font-size: clamp(30px, 5vw, 42px); font-weight: 500; letter-spacing: 0.08em;
       text-transform: uppercase; margin-top: 18px; line-height: 1.15; }
  .lede { font-style: italic; color: var(--ink-soft); margin-top: 6px; font-size: 18px; }
  .portrait { width: 132px; height: 156px; object-fit: cover; border: 1px solid var(--hairline);
              filter: grayscale(55%) sepia(6%); float: right; margin: 8px 0 14px 22px; }
  .bio { margin-top: 26px; font-size: 17.5px; line-height: 1.65; color: var(--ink-soft); }
  .ctas { margin: 28px 0 8px; display: flex; gap: 14px; flex-wrap: wrap; }
  .cta { display: inline-block; padding: 12px 24px; border: 1px solid var(--bronze);
         color: var(--bronze); text-decoration: none; font-size: 13.5px;
         letter-spacing: 0.18em; text-transform: uppercase; }
  .cta:hover { background: var(--bronze); color: var(--ivory); }
  .copyright-note { margin-top: 24px; font-style: italic; color: var(--ink-soft); }
  .work { margin-top: 54px; border-top: 1px solid var(--hairline); padding-top: 34px; }
  .work img { max-width: 100%; border: 1px solid var(--hairline); background: rgba(var(--paper), 1); }
  .work h2 { font-size: 25px; font-weight: 500; font-style: italic; margin-top: 16px; }
  .meta { color: var(--ink-soft); font-size: 15px; margin-top: 4px; }
  .meta span { display: inline-block; margin-right: 16px; }
  .work p { margin-top: 12px; font-size: 16.5px; line-height: 1.62; color: var(--ink-soft); }
  .fact { margin-top: 10px; }
  .fact a { font-size: 13px; font-style: italic; white-space: nowrap; }
  .work-attr { font-size: 12px !important; opacity: 0.7; }
  .work-attr a { color: inherit; }
  .attr { margin-top: 60px; font-size: 12.5px; color: var(--ink-soft); opacity: 0.8; }
  .attr a { color: inherit; }
  /* directory */
  .period { margin-top: 46px; border-top: 1px solid var(--hairline); padding-top: 26px; }
  .period h2 { font-size: 20px; letter-spacing: 0.2em; text-transform: uppercase; font-weight: 500; }
  .period .years { color: var(--bronze); font-size: 14px; letter-spacing: 0.12em; }
  .period p { margin-top: 10px; font-size: 16px; line-height: 1.6; color: var(--ink-soft); }
  .period ul { margin: 14px 0 0 0; padding: 0; list-style: none; }
  .period li { padding: 7px 0; border-bottom: 1px dotted var(--hairline); font-size: 17px; }
  .period li a { text-decoration: none; color: var(--ink); }
  .period li a:hover { color: var(--bronze); }
  .period li .sub { color: var(--ink-soft); font-size: 14px; font-style: italic; }
</style>"""


def esc(s):
    return html.escape(str(s or ""), quote=True)


def life(a):
    if not a.get("born"):
        return ""
    return f"{a['born']}–{a['died']}" if a.get("died") else f"b. {a['born']}"


def one_liner(a):
    import re
    return re.sub(r"\s*\((?:born |b\. )?\d{4}[^)]*\)", "", a.get("oneLiner") or "")


def head(title, desc, canonical, og_image):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:site_name" content="THEODORA">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&display=swap" rel="stylesheet">
{THEME_SNIPPET}
<link rel="stylesheet" href="/museum/css/museum-core.css">
{PAGE_CSS}
{GA_SNIPPET}"""


def artist_jsonld(a):
    works = []
    for p in a["paintings"]:
        w = {
            "@type": "VisualArtwork",
            "name": p["title"],
            "creator": {"@type": "Person", "name": a["name"]},
            "image": p["image"].get("thumb1600") or p["image"].get("thumb640"),
        }
        if p.get("year"):
            w["dateCreated"] = str(p["year"])
        if p.get("story"):
            w["description"] = p["story"]["extract"][:300]
        works.append(w)
    data = {
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "mainEntity": {
            "@type": "Person",
            "name": a["name"],
            "description": one_liner(a),
            "birthDate": str(a.get("born") or ""),
            "deathDate": str(a.get("died") or ""),
            "sameAs": a.get("wikipedia"),
            "image": (a.get("portrait") or {}).get("thumb"),
        },
        "hasPart": works,
        "isPartOf": {"@type": "CollectionPage", "name": "The Museum",
                     "url": f"{SITE}/museum/"},
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False) + "</script>")


def crumb(extra=""):
    return (f'<nav class="crumb"><a href="/">THEODORA</a> · '
            f'<a href="/museum/">The Museum</a> · '
            f'<a href="/museum/artists/">The Collection</a>{extra}</nav>')


def painting_block(p):
    img = p["image"]
    dims = f"{p['cm']['h']} × {p['cm']['w']} cm" if p.get("cm") else ""
    meta = "".join(f"<span>{esc(x)}</span>" for x in
                   [p.get("year"), dims, p.get("collection")] if x)
    story = (f"<p>{esc(p['story']['extract'])}</p>" if p.get("story") else "")
    facts = "".join(
        f'<p class="fact">{esc(f["text"])} '
        f'<a href="{esc(f["source"])}" target="_blank" rel="noopener">{esc(f["section"])} →</a></p>'
        for f in p.get("facts") or [])
    lic = p.get("license") or {}
    credit_bits = " · ".join(
        x for x in [lic.get("credit"), lic.get("name")]
        if x and not x.lower().startswith("unknown"))
    commons_url = ("https://commons.wikimedia.org/wiki/"
                   + urllib.parse.quote(img.get("file") or "", safe=":"))
    attr = (f'<p class="work-attr">{esc(credit_bits)}{" · " if credit_bits else ""}'
            f'<a href="{esc(commons_url)}" target="_blank" rel="noopener">Wikimedia Commons</a></p>')
    return f"""<section class="work">
<img loading="lazy" src="{esc(img.get('thumb640'))}" alt="{esc(p['title'])}">
<h2>{esc(p['title'])}</h2>
<div class="meta">{meta}</div>
{story}{facts}
{attr}
</section>"""


def build_artist(a):
    name = a["name"]
    desc_src = (a.get("bio") or {}).get("extract") or one_liner(a)
    desc = desc_src.split(". ")[0][:250] + "."
    og = ""
    if a["paintings"]:
        og = a["paintings"][0]["image"].get("thumb1600") or ""
    if not og:
        og = (a.get("portrait") or {}).get("thumb") or f"{SITE}/og-image.jpg"
    canonical = f"{SITE}/museum/artists/{a['slug']}/"

    if a["hasGallery"]:
        ctas = (f'<a class="cta" href="/museum/gallery/?artist={a["slug"]}">'
                f'Walk the 3D gallery · {len(a["paintings"])} works →</a>'
                f'<a class="cta" href="/museum/#artist={a["slug"]}">See on the timeline</a>')
        works = "".join(painting_block(p) for p in a["paintings"])
    else:
        ctas = f'<a class="cta" href="/museum/#artist={a["slug"]}">See on the timeline</a>'
        works = (f'<p class="copyright-note">The paintings are still under copyright '
                 f'and cannot be hung in this museum. '
                 f'<a href="{esc(a["wikipedia"])}" target="_blank" rel="noopener">'
                 f'View the work on Wikipedia →</a></p>')

    portrait = ""
    if (a.get("portrait") or {}).get("thumb"):
        portrait = (f'<img class="portrait" src="{esc(a["portrait"]["thumb"])}" '
                    f'alt="Portrait of {esc(name)}">')

    return f"""{head(f"{name} · The Museum · THEODORA", desc, canonical, og)}
{artist_jsonld(a)}
</head>
<body>
{crumb(f' · <span>{esc(name)}</span>')}
{portrait}
<h1>{esc(name)}</h1>
<p class="lede">{esc(', '.join(x for x in [one_liner(a), life(a)] if x))}</p>
<div class="bio">{esc((a.get('bio') or {}).get('extract') or '')}</div>
<div class="ctas">{ctas}</div>
{works}
<p class="attr">Text: <a href="{esc((a.get('bio') or {}).get('source') or a.get('wikipedia'))}"
target="_blank" rel="noopener">Wikipedia</a> (CC BY-SA 4.0) ·
Images: <a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">Wikimedia Commons</a>,
public domain or Creative Commons (attribution with each work) ·
Part of <a href="/museum/">The Museum</a> at THEODORA</p>
</body>
</html>
"""


def build_directory(index, artists_full):
    by_period = {}
    for a in index["artists"]:
        by_period.setdefault(a["periods"][0], []).append(a)

    sections = []
    for p in index["periods"]:
        arts = by_period.get(p["id"], [])
        if not arts:
            continue
        items = "".join(
            f'<li><a href="/museum/artists/{a["slug"]}/">{esc(a["name"])}</a> '
            f'<span class="sub">{esc(", ".join(x for x in [one_liner(a), life(a)] if x))}'
            f'{" · " + str(a["paintingCount"]) + " works in the gallery" if a["hasGallery"] else ""}'
            f'</span></li>'
            for a in sorted(arts, key=lambda x: x.get("born") or 0))
        sections.append(f"""<section class="period">
<h2>{esc(p['name'])} <span class="years">{p['start']}–{p['end']}</span></h2>
<p>{esc(p['summary'])}</p>
<ul>{items}</ul>
</section>""")

    n_gallery = sum(1 for a in index["artists"] if a["hasGallery"])
    desc = (f"The full collection of The Museum at THEODORA: {len(index['periods'])} periods of art "
            f"history and {len(index['artists'])} artists, {n_gallery} of them with walkable 3D "
            f"galleries of freely licensed works. All facts from Wikipedia.")
    jsonld = ('<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "The Collection · The Museum · THEODORA",
        "url": f"{SITE}/museum/artists/",
        "description": desc,
        "hasPart": [{"@type": "ProfilePage",
                     "url": f"{SITE}/museum/artists/{a['slug']}/",
                     "name": a["name"]} for a in index["artists"]],
        "license": "https://creativecommons.org/licenses/by-sa/4.0/",
    }, ensure_ascii=False) + "</script>")

    return f"""{head("The Collection · The Museum · THEODORA", desc, f"{SITE}/museum/artists/", f"{SITE}/og-image.jpg")}
{jsonld}
</head>
<body>
{crumb()}
<h1>The Collection</h1>
<p class="lede">{len(index['periods'])} periods · {len(index['artists'])} artists ·
{n_gallery} walkable 3D galleries. Every fact and image from Wikipedia and Wikimedia Commons.</p>
<div class="ctas"><a class="cta" href="/museum/">Open the interactive timeline →</a></div>
{''.join(sections)}
<p class="attr">Text: Wikipedia (CC BY-SA 4.0) · Images: Wikimedia Commons, public domain or
Creative Commons (attribution with each work) ·
Machine-readable data: <a href="/museum/data/index.json">index.json</a></p>
</body>
</html>
"""


def main():
    index = json.loads((DATA / "index.json").read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    count = 0
    artists_full = {}
    for ia in index["artists"]:
        a = json.loads((DATA / "artists" / f"{ia['slug']}.json").read_text(encoding="utf-8"))
        artists_full[ia["slug"]] = a
        d = OUT / ia["slug"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(build_artist(a), encoding="utf-8")
        count += 1
    (OUT / "index.html").write_text(build_directory(index, artists_full), encoding="utf-8")
    print(f"wrote {count} artist pages + the collection directory")


if __name__ == "__main__":
    main()
