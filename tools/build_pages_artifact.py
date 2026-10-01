#!/usr/bin/env python3
"""Build the GitHub Pages artifact: the public files of the site, nothing else.

The repo holds the built site and its sources side by side (page JSON, specs,
build scripts, tools, AGENTS.md). Branch-mode Pages served all of it. The
deploy workflow (.github/workflows/pages.yml) runs this script and publishes
only its output folder.

What is public is decided by rule, so new pages and assets deploy without
anyone editing a list:
  - any tracked file with a web extension (html, css, js, xml, images, fonts,
    video) outside the source folders in PRIVATE_DIRS;
  - the root text files crawlers read (ROOT_FILES) and the IndexNow key file;
  - runtime data folders the pages fetch (RUNTIME_DIRS) and vendor folders,
    copied whole;
  - .well-known/ if it ever exists.
Everything else (.py, .md specs, content/, templates/, tools/, other .json)
stays out.

Then it checks the artifact and exits 1 if:
  - a sitemap <loc>, or a link or asset referenced from a served page, CSS, JS
    or text file, exists in the repo but was left out of the artifact;
  - a sitemap <loc> does not exist at all;
  - a private file slipped in.
A reference missing from the repo as well is only a warning (the build's own
link gates own that).

  python3 tools/build_pages_artifact.py               # writes _site/
  python3 tools/build_pages_artifact.py --out DIR     # elsewhere
  python3 tools/build_pages_artifact.py --inventory F # also write every URL checked
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from urllib.parse import unquote, urljoin, urlsplit

HOST = "stavtheodor.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PUBLIC_EXT = {
    "html", "htm", "css", "js", "mjs", "xml",
    "jpg", "jpeg", "png", "webp", "gif", "svg", "avif", "ico",
    "woff2", "woff", "ttf", "otf",
    "mp4", "webm", "mp3", "m4a", "vtt", "pdf", "webmanifest",
}
# Sources and tooling: never served, whatever the extension.
PRIVATE_DIRS = ("content/", "templates/", "tools/", "museum/tools/", ".github/", "node_modules/")
# Fetched by page scripts at runtime (museum/js/shared/data.js), copied whole.
RUNTIME_DIRS = ("museum/data/",)
# Third-party code, copied whole (licence files included).
VENDOR_DIRS = ("js/vendor/", "museum/vendor/")
# Root files read by crawlers and listed in robots.txt.
ROOT_FILES = {"robots.txt", "llms.txt", "llms-full.txt", "agent.txt", "answers.md", "CNAME"}
# Never served, checked again after the copy.
PRIVATE_FILE = re.compile(r"(\.py|\.sh|\.gs|\.ipynb)$|(^|/)\.(?!well-known/)|(^|/)(AGENTS|CLAUDE|readme|README)\.md$")


def tracked_files(src):
    try:
        out = subprocess.run(["git", "-C", src, "ls-files", "-z"], check=True,
                             capture_output=True).stdout.decode()
        files = [f for f in out.split("\0") if f]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for dp, dn, fn in os.walk(src):
            dn[:] = [d for d in dn if d != ".git"]
            for f in fn:
                files.append(os.path.relpath(os.path.join(dp, f), src).replace(os.sep, "/"))
    return sorted(f for f in files if os.path.isfile(os.path.join(src, f)))


def is_indexnow_key(src, rel):
    if "/" in rel or not re.fullmatch(r"[0-9a-f]{8,128}\.txt", rel):
        return False
    with open(os.path.join(src, rel), encoding="utf-8", errors="replace") as fh:
        return fh.read().strip() == rel[:-4]


def is_public(src, rel):
    if rel.startswith(".well-known/"):
        return True
    if rel.startswith(PRIVATE_DIRS):
        return False
    if rel.startswith(RUNTIME_DIRS + VENDOR_DIRS):
        return True
    if rel in ROOT_FILES or is_indexnow_key(src, rel):
        return True
    if PRIVATE_FILE.search(rel):
        return False
    ext = rel.rsplit(".", 1)[-1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
    return ext in PUBLIC_EXT


# ---------- references ----------

ABS_URL = re.compile(r"https?://(?:www\.)?" + re.escape(HOST) + r"(/[^\s\"'<>()\\]*)?")
ATTR = re.compile(r"""\b(?:href|src|poster|data-src|action)\s*=\s*(["'])(.*?)\1""", re.I | re.S)
META_IMG = re.compile(r"""<meta[^>]+(?:property|name)\s*=\s*["'](?:og:image|og:image:url|og:image:secure_url|twitter:image|og:url|og:video|thumbnail)["'][^>]*>""", re.I)
META_CONTENT = re.compile(r"""\bcontent\s*=\s*(["'])(.*?)\1""", re.I | re.S)
SRCSET = re.compile(r"""\b(?:srcset|data-srcset|imagesrcset)\s*=\s*(["'])(.*?)\1""", re.I | re.S)
CSS_URL = re.compile(r"""url\(\s*(["']?)([^)"']+)\1\s*\)""", re.I)
QUOTED_PATH = re.compile(r"""["'`](/[A-Za-z0-9_\-./%]*[A-Za-z0-9_\-]\.[A-Za-z0-9]{2,12})["'`]""")
JS_IMPORT = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s+)["'](\.{1,2}/[^"']+)["']""")


def refs_in(rel, text):
    """(base url path, reference) pairs found in one served text file."""
    base = "/" + rel
    ext = rel.rsplit(".", 1)[-1].lower()
    found = set()
    for m in ABS_URL.finditer(text):
        found.add((m.group(1) or "/").rstrip(".,;:!?"))
    if ext in ("html", "htm", "xml", "svg"):
        for m in ATTR.finditer(text):
            found.add(m.group(2).strip())
        for m in META_IMG.finditer(text):
            c = META_CONTENT.search(m.group(0))
            if c:
                found.add(c.group(2).strip())
        for m in SRCSET.finditer(text):
            for part in m.group(2).split(","):
                part = part.strip().split()
                if part:
                    found.add(part[0])
    if ext in ("html", "htm", "css", "svg"):
        for m in CSS_URL.finditer(text):
            found.add(m.group(2).strip())
    if ext in ("html", "htm", "js", "mjs"):
        for m in QUOTED_PATH.finditer(text):
            found.add(m.group(1))
    if ext in ("js", "mjs"):
        for m in JS_IMPORT.finditer(text):
            found.add(m.group(1))
    out = set()
    for r in found:
        r = r.replace("&amp;", "&")
        if not r or r.startswith(("#", "mailto:", "tel:", "data:", "javascript:", "blob:", "sms:", "whatsapp:")):
            continue
        if "{" in r or "' +" in r:
            continue
        u = urlsplit(urljoin("https://" + HOST + base, r))
        if u.scheme not in ("http", "https") or u.hostname not in (HOST, "www." + HOST):
            continue
        out.add(unquote(u.path) or "/")
    return out


def resolve(tree, path):
    """Path on disk under tree that a URL path is served from, or None."""
    rel = path.lstrip("/")
    cand = []
    if rel == "" or rel.endswith("/"):
        cand.append(rel + "index.html")
    else:
        cand.append(rel)
        cand.append(rel + "/index.html")  # Pages redirects /x to /x/
        cand.append(rel + ".html")  # and serves /x from x.html
    for c in cand:
        if os.path.isfile(os.path.join(tree, c)):
            return c
    return None


def sitemap_locs(tree):
    locs = set()
    for f in sorted(os.listdir(tree)):
        if re.fullmatch(r"sitemap[^/]*\.xml", f):
            with open(os.path.join(tree, f), encoding="utf-8") as fh:
                for m in re.finditer(r"<loc>\s*([^<\s]+)\s*</loc>", fh.read()):
                    u = urlsplit(m.group(1))
                    if u.hostname in (HOST, "www." + HOST):
                        locs.add(unquote(u.path) or "/")
    return locs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", default=ROOT)
    ap.add_argument("--out", default=os.path.join(ROOT, "_site"))
    ap.add_argument("--inventory", help="write every URL path checked, one per line")
    a = ap.parse_args()
    src, out = os.path.abspath(a.src), os.path.abspath(a.out)
    if out == src or src.startswith(out + os.sep):
        sys.exit("--out must not contain the source tree")

    files = tracked_files(src)
    public = [f for f in files if is_public(src, f)]
    private = [f for f in files if f not in set(public)]
    if os.path.isdir(out):
        shutil.rmtree(out)
    for f in public:
        dst = os.path.join(out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(src, f), dst)

    errors, warnings = [], []
    for f in public:
        if f.startswith(PRIVATE_DIRS) or (PRIVATE_FILE.search(f) and not f.startswith(VENDOR_DIRS)):
            errors.append("private file in artifact: " + f)

    locs = sitemap_locs(out)
    for p in sorted(locs):
        if resolve(out, p):
            continue
        if resolve(src, p):
            errors.append("sitemap URL left out of the artifact: " + p)
        else:
            errors.append("sitemap URL with no file: " + p)

    referenced = {}
    for f in public:
        ext = f.rsplit(".", 1)[-1].lower()
        if ext not in ("html", "htm", "css", "js", "mjs", "xml", "svg", "txt", "md", "webmanifest"):
            continue
        if f.startswith(VENDOR_DIRS) or f.startswith(RUNTIME_DIRS):
            continue  # third-party code and fetched data are not link sources
        with open(os.path.join(out, f), encoding="utf-8", errors="replace") as fh:
            for p in refs_in(f, fh.read()):
                referenced.setdefault(p, f)
    for p, where in sorted(referenced.items()):
        if resolve(out, p):
            continue
        if resolve(src, p):
            errors.append("referenced from /%s but left out of the artifact: %s" % (where, p))
        else:
            warnings.append("referenced from /%s, no such file in the repo: %s" % (where, p))

    if a.inventory:
        urls = set(locs) | set(referenced) | {"/" + f for f in public}
        urls = {u for u in urls if resolve(out, u)}
        with open(a.inventory, "w", encoding="utf-8") as fh:
            fh.write("\n".join(sorted(urls)) + "\n")

    for w in warnings:
        print("warning: " + w)
    for e in errors:
        print("ERROR: " + e)
    print("pages artifact: %d public files, %d left out, %d sitemap URLs, %d references checked%s"
          % (len(public), len(private), len(locs), len(referenced),
             "" if not errors else ", %d errors" % len(errors)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
