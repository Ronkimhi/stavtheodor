#!/usr/bin/env python3
"""Tile images for the homepage's industries section (build-home.py INDUSTRIES, 2026-09-28).

    python3 tools/make_industry_thumbs.py

For each buyer variant, the after image of its first room (content/variants/<id>.json rooms[0].a, or the room
TILE_ROOM names),
or the homepage's first room for a variant without rooms, cropped to 3:2 around the room's focal
point and saved as images/home2/industries/<id>.webp at 900 by 600, WebP quality 82 (2026-10-06, Ron's image-quality
fix: until then 600 by 400 at quality 72; the tiles show at the same size, the file is sharper on 1.5x and 2x screens).
It crops from the room's 2400 px twin when there is one, else from the 1800 px file. Run it again when a variant's
first room changes, and commit the images. Needs Pillow (a developer tool: the build itself only checks that the files
exist). images/home2/industries/designers.webp: the designers tile links /for-designers/ since /designers/ stopped being
a variant (2026-09-29, build-home.py INDUSTRY_PAGES); it is cut from the homepage's first room (HOME_TILES).
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, QUALITY = 900, 600, 82
# A tile cut from another room than the variant's first (index into its rooms). hotels: the olive and burgundy
# lounge (hotels_s1), Ron's pick for the Boutique hotels tile on 2026-09-29; /hotels/ still opens on its first room.
TILE_ROOM = {'hotels': 1}
# Tiles kept by hand, never written here: investment-firms.webp is Ron's pick of 2026-09-29 (a dining room with an olive
# tree, a round walnut table and a framed cactus collage), resized whole from a 1536 by 1024 source at the same 600 by
# 400, quality 78 (about 28 KB); /investment-firms/ still opens on its own first room. Since 2026-10-06 it is 900 by 600
# at quality 82, resized whole from the same source (wealth-meeting-room-goodman.png in Ron's Downloads).
BY_HAND = {'investment-firms'}
HOME_TILES = ('designers',)  # tiles with no variant JSON, cut from the homepage's first room


def home_first_room():
    js = open(os.path.join(ROOT, 'js', 'home-opening.js'), encoding='utf-8').read()
    m = re.search(r"land: \{ b: '[^']+', a: '([^']+)'[^}]*?fx: ([\d.]+), fy: ([\d.]+)", js)
    return m.group(1), float(m.group(2)), float(m.group(3))


def best_source(a):
    """The room's 2400 px twin when it has one, else the file itself (paths under images/home2/)."""
    hi = os.path.join(ROOT, 'images', 'home2', re.sub(r'\.webp$', '-2400.webp', a))
    return hi if os.path.isfile(hi) else os.path.join(ROOT, 'images', 'home2', a)


def main():
    out_dir = os.path.join(ROOT, 'images', 'home2', 'industries')
    os.makedirs(out_dir, exist_ok=True)
    home = home_first_room()
    jobs = [{'id': t} for t in HOME_TILES]
    for f in sorted(os.listdir(os.path.join(ROOT, 'content', 'variants'))):
        if f.endswith('.json'):
            jobs.append(json.load(open(os.path.join(ROOT, 'content', 'variants', f), encoding='utf-8')))
    for v in jobs:
        if v['id'] in BY_HAND:
            continue
        rooms = v.get('rooms') or []
        r = rooms[TILE_ROOM.get(v['id'], 0)] if rooms else None
        a, fx, fy = (r['a'], r['fx'], r['fy']) if r else home
        src = best_source(a)
        im = Image.open(src).convert('RGB')
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
        print(f'{os.path.relpath(dest, ROOT)} from {os.path.relpath(src, os.path.join(ROOT, "images", "home2"))}, {os.path.getsize(dest) // 1024} KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
