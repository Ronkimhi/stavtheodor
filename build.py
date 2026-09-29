#!/usr/bin/env python3
"""The one build command for stavtheodor.com. Run from the repo root:

    python3 build.py

Runs, in order:
  build-site-pages.py      advisory, projects, partners, guide and local pages and their hubs,
                           then build-post-pages.py: radar/<slug>/, radar/
  tools/check_variants.py  the buyer variants of the homepage, content/variants/*.json (none is fine)
  build-home.py            index.html from templates/home.html + content/, the redirect stubs, and
                           one indexable page per buyer variant at /<path>/
  tools/build_sitemap.py   sitemap.xml (an index) over sitemap-pages.xml, sitemap-radar.xml, sitemap-museum.xml
  tools/check_site.py      the gates: dashes, phone numbers, language twins, anchors, links, JSON-LD,
                           FAQ mirror, noindex, removed assets, language default, sitemap, variants

Every generated page is written fresh; never hand-edit one.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
for step in (['build-site-pages.py'], ['tools/check_variants.py'], ['build-home.py'], ['tools/build_sitemap.py'], ['tools/check_site.py']):
    print(f'\n== {" ".join(step)} ==')
    subprocess.run([sys.executable] + step, check=True)
print('\nBuild complete.')
