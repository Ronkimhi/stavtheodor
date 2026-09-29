#!/usr/bin/env python3
"""Tile images for the homepage's industries section (build-home.py INDUSTRIES, 2026-09-28).

    python3 tools/make_industry_thumbs.py

For each buyer variant, the after image of its first room (content/variants/<id>.json rooms[0].a),
or the homepage's first room for a variant without rooms, cropped to 3:2 around the room's focal
point and saved as images/home2/industries/<id>.webp at 600 by 400 (about 30 to 60 KB). Run it
again when a variant's first room changes, and commit the images. Needs Pillow (a developer tool:
the build itself only checks that the files exist). images/home2/industries/designers.webp is kept by hand: the
designers tile links /for-designers/ since /designers/ stopped being a variant (2026-09-29, build-home.py INDUSTRY_PAGES),
so this script no longer writes it; it was cut from the homepage's first room, as above.
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, QUALITY = 600, 400, 72


def home_first_room():
    js = open(os.path.join(ROOT, 'js', 'home-opening.js'), encoding='utf-8').read()
    m = re.search(r"land: \{ b: '[^']+', a: '([^']+)'[^}]*?fx: ([\d.]+), fy: ([\d.]+)", js)
    return m.group(1), float(m.group(2)), float(m.group(3))


def main():
    out_dir = os.path.join(ROOT, 'images', 'home2', 'industries')
    os.makedirs(out_dir, exist_ok=True)
    home = home_first_room()
    for f in sorted(os.listdir(os.path.join(ROOT, 'content', 'variants'))):
        if not f.endswith('.json'):
            continue
        v = json.load(open(os.path.join(ROOT, 'content', 'variants', f), encoding='utf-8'))
        rooms = v.get('rooms') or []
        a, fx, fy = (rooms[0]['a'], rooms[0]['fx'], rooms[0]['fy']) if rooms else home
        im = Image.open(os.path.join(ROOT, 'images', 'home2', a)).convert('RGB')
        iw, ih = im.size
        if iw / ih > W / H:  # wider than 3:2: crop the width around fx
            cw = round(ih * W / H)
            x0 = min(max(0, round(fx * iw - cw / 2)), iw - cw)
            im = im.crop((x0, 0, x0 + cw, ih))
        else:
            ch = round(iw * H / W)
            y0 = min(max(0, round(fy * ih - ch / 2)), ih - ch)
            im = im.crop((0, y0, iw, y0 + ch))
        im = im.resize((W, H), Image.LANCZOS)
        dest = os.path.join(out_dir, v['id'] + '.webp')
        im.save(dest, 'WEBP', quality=QUALITY, method=6)
        print(f'{os.path.relpath(dest, ROOT)} from {a}, {os.path.getsize(dest) // 1024} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
