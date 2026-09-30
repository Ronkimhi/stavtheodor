#!/usr/bin/env python3
"""The one build command for stavtheodor.com. Run from the repo root:

    python3 build.py

Runs, in order:
  build-site-pages.py      advisory, projects, partners, guide and local pages and their hubs,
                           then build-post-pages.py: radar/<slug>/, radar/
  tools/check_variants.py  the buyer variants of the homepage, content/variants/*.json (none is fine)
  build-home.py            index.html from templates/home.html + content/, the redirect stubs, and
                           one indexable page per buyer variant at /<path>/
  museum/tools/build_artist_pages.py
                           museum/artists/ (the collection and one page per artist, from museum/data/),
                           through the same dash sanitizer, phone and entity graph (2026-09-29)
  tools/build_llms_full.py llms-full.txt, the English text of every content/pages/*.json page, for LLMs (2026-09-30)
  tools/build_sitemap.py   sitemap.xml (an index) over sitemap-pages.xml, sitemap-radar.xml, sitemap-museum.xml
  tools/check_site.py      the gates: dashes, phone numbers, language twins, anchors, links, JSON-LD,
                           FAQ mirror, noindex, removed assets, language default, sitemap, variants,
                           and since 2026-09-29 the business phone, the NAP link and one JSON-LD graph per page
  tools/check_sameas.py    asks every sameAs URL in content/entity.json whether it answers; prints the dead
                           ones and never fails the build (no network: it says so and skips)

Every generated page is written fresh; never hand-edit one.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
for step in (['build-site-pages.py'], ['tools/check_variants.py'], ['build-home.py'], ['museum/tools/build_artist_pages.py'],
             ['tools/build_llms_full.py'], ['tools/build_sitemap.py'], ['tools/check_site.py'], ['tools/check_sameas.py']):
    print(f'\n== {" ".join(step)} ==')
    subprocess.run([sys.executable] + step, check=True)
print('\nBuild complete.')
