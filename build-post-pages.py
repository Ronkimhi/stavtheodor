#!/usr/bin/env python3
"""
Generates a real, standalone, indexable URL for every Art Radar post
(radar/<slug>/index.html) from the single index.html source of truth,
and refreshes sitemap.xml to list every post URL.

Run this after adding a new post block to index.html, before deploying.
The homepage itself (index.html) is never restructured — this only adds
extra pages and rewrites two pieces of metadata inside index.html:
  - each post's JSON-LD `url` / `mainEntityOfPage` (fragment -> real URL)
  - a small "Permalink" link under each post's date

Everything else on the homepage (layout, content, styling) is untouched.
"""
import re
import json
import os

SITE = "https://stavtheodor.com"
SRC = "index.html"
OUT_DIR = "radar"

html = open(SRC, encoding="utf-8", newline="").read()

style_block = re.search(r"<style>.*?</style>", html, re.S).group(0)

entity_graph_script = re.search(
    r'<!-- Structured data: Person \+ Organization \+ WebSite \(JSON-LD\) -->\r?\n<script type="application/ld\+json">.*?</script>',
    html, re.S,
).group(0)

FAVICONS = """<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Frank+Ruhl+Libre:wght@300;400;500&display=swap" rel="stylesheet">"""

LANG_TOGGLE = """<div class="lang-switch" role="group" aria-label="Choose post language">
    <button type="button" data-lang="he" class="active">עברית</button>
    <button type="button" data-lang="en">English</button>
  </div>"""

LANG_JS = """<script>
(function () {
  function apply(lang) {
    document.body.classList.toggle('lang-en', lang === 'en');
    document.querySelectorAll('.lang-switch button').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-lang') === lang);
    });
  }
  var saved = 'he';
  try { saved = localStorage.getItem('radarLang') || 'he'; } catch (e) {}
  if (saved === 'en') { apply('en'); }
  document.querySelectorAll('.lang-switch button').forEach(function (b) {
    b.addEventListener('click', function () {
      var lang = b.getAttribute('data-lang');
      try { localStorage.setItem('radarLang', lang); } catch (e) {}
      apply(lang);
    });
  });
})();
</script>"""

GA_SNIPPET = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-4300MN0Q97"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-4300MN0Q97');
</script>"""

FOOTER = """<footer id="contact">
  <div class="wrap">
    <div class="name">Stav Theodor&#8209;Kimhi</div>
    <div class="sub">Art Curation &amp; Advisory &middot; Tenafly, New Jersey</div>
    <ul class="contact-list">
      <li><a href="mailto:stavtheodor85@gmail.com">stavtheodor85@gmail.com</a></li>
      <li><a href="tel:+15512466416">+1 (551) 246-6416</a></li>
      <li><a href="https://chat.whatsapp.com/CapF9HczSoL4szwUKKtkq5" target="_blank" rel="noopener">Art Radar on WhatsApp</a></li>
      <li><a href="/#portfolio">Portfolio</a></li>
    </ul>
    <div class="copyright">&copy; 2026 THEODORA</div>
  </div>
</footer>"""

posts_section = re.search(r'<section id="posts".*?</section>', html, re.S).group(0)

pair_re = re.compile(
    r'<script type="application/ld\+json">\s*(.*?)\s*</script>\s*'
    r'<article class="(post[^"]*)" id="([a-z0-9\-]+)">(.*?)</article>',
    re.S,
)
pairs = pair_re.findall(posts_section)
if not pairs:
    raise SystemExit("No posts found — check the regex against index.html structure.")

posts = []
for json_text, article_class, slug, article_inner in pairs:
    data = json.loads(json_text)
    img_match = re.search(r'<img src="([^"]+)"', article_inner)
    og_image = f"{SITE}/{img_match.group(1)}" if img_match else f"{SITE}/og-image.jpg"
    posts.append({
        "slug": slug,
        "article_class": article_class,
        "headline": data["headline"],
        "description": data["description"],
        "datePublished": data["datePublished"],
        "dateModified": data.get("dateModified", data["datePublished"]),
        "json_text": json_text,
        "article_inner": article_inner,
        "og_image": og_image,
    })

print(f"Found {len(posts)} posts")

# ---- 1. Rewrite JSON-LD url/mainEntityOfPage in index.html to real permalinks ----
# Safe to re-run: posts already using the real permalink (from a prior run, or
# because the post was authored with the real URL directly) are left untouched.
new_html = html
for p in posts:
    frag_url = f"{SITE}/#{p['slug']}"
    real_url = f"{SITE}/radar/{p['slug']}/"
    old_json = p["json_text"]
    new_json = old_json.replace(
        f'"url": "{frag_url}"', f'"url": "{real_url}"'
    ).replace(
        f'"mainEntityOfPage": "{frag_url}"', f'"mainEntityOfPage": "{real_url}"'
    )
    if new_json != old_json:
        new_html = new_html.replace(old_json, new_json, 1)

# ---- 2. Add a small permalink link under each post's date (visual, minimal) ----
# Safe to re-run: skips any post that already has its permalink link.
for p in posts:
    if f'href="/radar/{p["slug"]}/"' in new_html:
        continue
    old_date_div = re.search(
        rf'(<article class="post[^"]*" id="{re.escape(p["slug"])}">\s*<div class="post-date">)([^<]*)(</div>)',
        new_html,
    )
    if old_date_div:
        replacement = (
            f'{old_date_div.group(1)}{old_date_div.group(2)}{old_date_div.group(3)}'
            f'\n    <a class="permalink" href="/radar/{p["slug"]}/">Permalink</a>'
        )
        new_html = new_html.replace(old_date_div.group(0), replacement, 1)

# add minimal CSS for .permalink once, right before </style>
if ".permalink" not in new_html:
    new_html = new_html.replace(
        "</style>",
        "  .permalink { display: inline-block; margin-top: 6px; font-size: 11px; "
        "letter-spacing: 0.12em; text-transform: uppercase; color: var(--bronze); "
        "text-decoration: none; }\n  .permalink:hover { text-decoration: underline; }\n</style>",
        1,
    )

open(SRC, "w", encoding="utf-8", newline="").write(new_html)
print("index.html updated (JSON-LD permalinks + permalink links)")

# ---- 3. Generate radar/<slug>/index.html for every post ----
os.makedirs(OUT_DIR, exist_ok=True)

def render_post_page(p, all_posts):
    permalink = f"{SITE}/radar/{p['slug']}/"
    updated_json = p["json_text"].replace(
        f'"url": "{SITE}/#{p["slug"]}"', f'"url": "{permalink}"'
    ).replace(
        f'"mainEntityOfPage": "{SITE}/#{p["slug"]}"', f'"mainEntityOfPage": "{permalink}"'
    )

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "THEODORA", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Art Radar", "item": SITE + "/#radar"},
            {"@type": "ListItem", "position": 3, "name": p["headline"], "item": permalink},
        ],
    }

    others = [o for o in all_posts if o["slug"] != p["slug"]][:8]
    more_links = "\n".join(
        f'      <li><a href="/radar/{o["slug"]}/">{o["headline"]}</a></li>' for o in others
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['headline']} &middot; Art Radar &middot; THEODORA</title>
{FAVICONS}
<meta name="description" content="{p['description']}">
<meta property="og:title" content="{p['headline']}">
<meta property="og:description" content="{p['description']}">
<meta property="og:type" content="article">
<meta property="og:url" content="{permalink}">
<meta property="og:image" content="{p['og_image']}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="THEODORA">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{p['headline']}">
<meta name="twitter:description" content="{p['description']}">
<meta name="twitter:image" content="{p['og_image']}">
<link rel="canonical" href="{permalink}">
{style_block}
<script type="application/ld+json">
{updated_json}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb, indent=2)}
</script>
{entity_graph_script}
</head>
<body>

<nav>
  <a href="/">Home</a>
  <a href="/#about">About</a>
  <a href="/#radar">Art Radar</a>
  <a href="/#contact">Contact</a>
</nav>

<header class="hero wrap" style="padding: 56px 24px 40px;">
  <a href="/" style="text-decoration:none; display:inline-block;">
    <img class="hero-logo" src="/images/theodora-logo.png" alt="THEODORA &middot; fine art living" width="440" height="195" style="width:150px; height:auto;">
  </a>
</header>

<hr class="divider">

<section id="posts" class="wrap">
  {LANG_TOGGLE}
  <article class="{p['article_class']}" id="{p['slug']}">{p['article_inner']}</article>
</section>

<hr class="divider">

<section class="wrap" style="padding: 40px 0 64px;">
  <div class="label">More from Art Radar</div>
  <ul style="margin-top: 16px; line-height: 2;">
{more_links}
  </ul>
  <p style="margin-top: 24px;"><a href="/#radar">&larr; Full Art Radar archive</a></p>
</section>

<hr class="divider">

{FOOTER}

{GA_SNIPPET}

{LANG_JS}

</body>
</html>
"""

for p in posts:
    post_dir = os.path.join(OUT_DIR, p["slug"])
    os.makedirs(post_dir, exist_ok=True)
    out_path = os.path.join(post_dir, "index.html")
    page = render_post_page(p, posts).replace("\r\n", "\n")
    open(out_path, "w", encoding="utf-8", newline="\n").write(page)
    print(f"  wrote {out_path}")

# ---- 4. Rewrite sitemap.xml with homepage + every post URL ----
latest = max(p["dateModified"] for p in posts)
url_entries = [f"""  <url>
    <loc>{SITE}/</loc>
    <lastmod>{latest}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>"""]
for p in sorted(posts, key=lambda x: x["datePublished"], reverse=True):
    url_entries.append(f"""  <url>
    <loc>{SITE}/radar/{p['slug']}/</loc>
    <lastmod>{p['dateModified']}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(url_entries)
    + "\n</urlset>\n"
)
open("sitemap.xml", "w", encoding="utf-8").write(sitemap)
print(f"sitemap.xml updated with {len(posts) + 1} URLs")
