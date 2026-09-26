#!/usr/bin/env python3
"""The one build command for stavtheodor.com. Run from the repo root:

    python3 build.py

Runs, in order:
  build-site-pages.py   advisory, projects, partners, guide pages and their hubs,
                        then build-post-pages.py: radar/<slug>/, radar/, sitemap.xml
  build-home.py         index.html from templates/home.html + content/, and the /2/ redirects
  tools/check_site.py   the gates: dashes, phone numbers, language twins, anchors, links, JSON-LD, FAQ mirror

Every generated page is written fresh; never hand-edit one.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
for step in (['build-site-pages.py'], ['build-home.py'], ['tools/check_site.py']):
    print(f'\n== {" ".join(step)} ==')
    subprocess.run([sys.executable] + step, check=True)
print('\nBuild complete.')
