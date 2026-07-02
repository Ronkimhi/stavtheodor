#!/usr/bin/env python3
"""
fetch_museum_data.py — builds museum/data/ from Wikipedia, Wikidata and Wikimedia Commons.

Everything written to the data files is sourced verbatim from those APIs:
this script selects and trims text at sentence boundaries, it never writes
its own prose. Re-runnable; raw API responses are cached in tools/cache/.

Usage:  python3 fetch_museum_data.py [--no-cache] [--artist SLUG[,SLUG...]]
"""

import hashlib
import html as html_lib
import json
import re
import subprocess
import sys
import time
import unicodedata
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
CACHE = HERE / "cache"
UA = "TheodoraMuseumBot/1.0 (https://stavtheodor.com; ronkkimhi@gmail.com)"
SLEEP = 0.5          # seconds between uncached requests
SPARQL_SLEEP = 1.0
MIN_PAINTINGS = 4    # below this an artist is placard-only (hasGallery: false)
DEFAULT_MAX = 10
CURRENT_YEAR = 2026

# Licenses we accept from Commons: public domain marks plus attribution-style
# Creative Commons (CC BY, CC BY-SA). Attribution is shown on every placard.
# NC/ND variants are always rejected.
FREE_LICENSES = ("public domain", "pd", "cc0", "no restrictions", "cc by", "attribution")
BLOCKED_LICENSE = re.compile(r"by-nc|by-nd|\bnc\b|\bnd\b", re.I)
# P31 type labels that mean the Wikidata "work" is really a venue, not a work.
NON_WORK_TYPES = re.compile(r"building|church|museum|street|square|house|chapel", re.I)
SECTION_STOPLIST = {
    "references", "external links", "see also", "notes", "further reading",
    "sources", "bibliography", "citations", "footnotes", "gallery", "works cited",
}
PREFERRED_SECTIONS = [
    "provenance", "history", "theft", "reception", "legacy", "analysis",
    "interpretation", "description", "background", "condition", "influence",
]

USE_CACHE = "--no-cache" not in sys.argv
_last_req = [0.0]

# The corporate DNS resolver on this machine intermittently returns nothing
# for Wikimedia domains while the network path itself is fine. When curl fails
# to resolve, retry once with the host pinned to Wikimedia's stable LB IPs.
WMF_PINS = {
    "en.wikipedia.org": "208.80.154.224",
    "commons.wikimedia.org": "208.80.154.224",
    "www.wikidata.org": "208.80.154.224",
    "query.wikidata.org": "208.80.154.224",
    "upload.wikimedia.org": "208.80.154.240",
}


def http_get(url, headers=None, sleep=SLEEP):
    key = hashlib.sha1(url.encode()).hexdigest()
    cf = CACHE / (key + ".json")
    if USE_CACHE and cf.exists():
        return cf.read_text(encoding="utf-8")
    wait = _last_req[0] + sleep - time.time()
    if wait > 0:
        time.sleep(wait)
    # curl instead of urllib: the corporate TLS-inspection cert chain on this
    # machine fails Python's OpenSSL verification but is trusted by the system.
    base = ["curl", "-sS", "--fail-with-body", "--max-time", "60", "-A", UA]
    for k, v in (headers or {}).items():
        base += ["-H", f"{k}: {v}"]
    host = urllib.parse.urlsplit(url).hostname or ""
    attempts = [base]
    if host in WMF_PINS:
        attempts.append(base + ["--resolve", f"{host}:443:{WMF_PINS[host]}"])
    r = None
    for cmd in attempts:
        r = subprocess.run(cmd + ["-w", "\n%{http_code}", url],
                           capture_output=True, text=True)
        if r.returncode not in (6, 28):  # 6 = could not resolve, 28 = timeout
            break
    out = r.stdout
    body, _, code = out.rpartition("\n")
    if code == "404":
        body = ""
    elif not code.startswith("2"):
        raise RuntimeError(f"HTTP {code or r.returncode} for {url}: {r.stderr[:200]}")
    _last_req[0] = time.time()
    cf.write_text(body, encoding="utf-8")
    return body


def get_json(url, sleep=SLEEP):
    body = http_get(url, headers={"Accept": "application/json"}, sleep=sleep)
    return json.loads(body) if body else None


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ɏ\"'(])", text)
    return [p.strip() for p in parts if len(p.strip()) > 2]


def first_sentences(text, n=2, max_chars=420):
    out, total = [], 0
    for s in sentences(text):
        # always keep the first sentence, even when it alone busts the budget
        # (several period leads run past 320 chars in a single sentence)
        if out and (len(out) >= n or total + len(s) > max_chars):
            break
        out.append(s)
        total += len(s)
    return " ".join(out)


def strip_html(s):
    return re.sub(r"<[^>]+>", "", s or "").strip()


def norm_label(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


# ---------- Wikipedia ----------

def wp_summary(title):
    return get_json(
        "https://en.wikipedia.org/api/rest_v1/page/summary/"
        + urllib.parse.quote(title.replace(" ", "_"), safe="")
    )


def wp_qid(title):
    d = get_json(
        "https://en.wikipedia.org/w/api.php?action=query&prop=pageprops"
        "&ppprop=wikibase_item&redirects=1&format=json&titles="
        + urllib.parse.quote(title, safe="")
    )
    for page in d["query"]["pages"].values():
        return page.get("pageprops", {}).get("wikibase_item")
    return None


# Files that illustrate an article but are not artworks: maps, flags, plans,
# diagrams, logos, audio, vector graphics.
NON_ARTWORK_FILE = re.compile(
    r"\.(svg|gif|ogg|oga|ogv|webm|pdf|djvu|mid)$"
    r"|map|locator|logo|flag|icon|seal|coat[_ ]of[_ ]arms|diagram|plan[_ ]of"
    r"|layout|chart|graph|scheme|reconstruction[_ ]drawing|timeline",
    re.I,
)


def wp_article_images(title):
    """File titles used on the entity's own Wikipedia article, in page order.
    For monuments, sites and cultures these are the images that editors chose
    to illustrate the subject, which is the closest thing to a curated set."""
    d = get_json(
        "https://en.wikipedia.org/w/api.php?action=query&prop=images"
        "&imlimit=100&redirects=1&format=json&titles="
        + urllib.parse.quote(title, safe="")
    )
    if not d:
        return []
    files = []
    for page in d["query"]["pages"].values():
        for im in page.get("images", []):
            f = im.get("title", "")
            if f.startswith("File:") and not NON_ARTWORK_FILE.search(f):
                files.append(f)
    return files


def wp_article_captions(title):
    """File title -> the caption Wikipedia editors wrote for that image on the
    entity's own article (figures, gallery boxes and legacy thumbs). The caption
    describes the specific view in plain language, which is exactly what the
    placard of an article-harvested work needs."""
    d = get_json(
        "https://en.wikipedia.org/w/api.php?action=parse&prop=text"
        "&redirects=1&format=json&formatversion=2&page="
        + urllib.parse.quote(title, safe="")
    )
    html = (d or {}).get("parse", {}).get("text", "")
    if not html:
        return {}

    blocks = re.findall(r"<figure[^>]*>.*?</figure>", html, re.S)
    blocks += re.findall(r'<li class="gallerybox".*?</li>', html, re.S)
    blocks += re.findall(r'<div class="thumb[^"]*".*?</div>\s*</div>\s*</div>', html, re.S)
    caps = {}
    for block in blocks:
        fm = re.search(r'/wiki/File:([^"&?#]+)', block)
        cm = (re.search(r"<figcaption[^>]*>(.*?)</figcaption>", block, re.S)
              or re.search(r'<div class="gallerytext"[^>]*>(.*?)</div>', block, re.S)
              or re.search(r'<div class="thumbcaption"[^>]*>(.*?)</div>', block, re.S))
        if not (fm and cm):
            continue
        f = "File:" + urllib.parse.unquote(fm.group(1)).replace("_", " ")
        cap = tidy_text(re.sub(r"\[\d+\]", "", cm.group(1)))
        if cap and f not in caps:
            caps[f] = cap
    return caps


def tidy_text(s):
    """Tag-stripped wiki text keeps entity refs and the spacing of removed
    links; normalize it into plain prose."""
    s = html_lib.unescape(strip_html(s or ""))
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([,.;:!?)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.strip()


# Commons file descriptions that carry no information for a visitor.
BOILERPLATE_DESC = re.compile(r"^(photograph|photo|picture|image|scan)s?[\s;.,]*", re.I)


# Photographer's processing and gear notes that ride along in descriptions.
RETOUCH_NOTE = re.compile(
    r"crop|retouch|levels? adjust|masked out|stitch|denoise|white balance"
    r"|edited|upscaled|sharpened|camera|\biso\s?\d|\blens\b|exposure|f/\d", re.I)


def usable_desc(s):
    """Commons ImageDescription values range from curated prose to camera noise;
    keep only readable English-looking sentences of placard length."""
    s = tidy_text(s)
    if not s or BOILERPLATE_DESC.fullmatch(s):
        return None
    kept = [x for x in sentences(s) if not RETOUCH_NOTE.search(x)][:2]
    s = first_sentences(" ".join(kept), n=2, max_chars=350)
    if len(s) < 30:
        return None
    if sum(1 for c in s if c.isascii()) / len(s) < 0.85:
        return None
    return s


def junk_title(t):
    """Camera-filename titles (2N9A6519-Pano, MET DP116347, DSC 0042) say
    nothing on a placard; detect tokens that mix letters with digit runs."""
    return bool(
        re.search(r"\b(?:IMG|DSCF?|DSCN|PICT)\b", t, re.I)
        or re.search(r"\b(?=[A-Za-z0-9-]*[A-Za-z])[A-Za-z0-9-]*\d{3,}[A-Za-z0-9-]*\b", t)
    )


def title_from_caption(cap):
    # sentence-split, but not after "c."/"ca." (circa) date abbreviations
    t = re.split(r"(?<!\bc\.)(?<!\bca\.)(?<=[.!?])\s", cap)[0]
    if len(t) > 80:
        t = t[:80].rsplit(" ", 1)[0] + "…"
    return t.rstrip(" .,;")


def wp_full_extract(title):
    d = get_json(
        "https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
        "&explaintext=1&redirects=1&format=json&titles="
        + urllib.parse.quote(title, safe="")
    )
    for page in d["query"]["pages"].values():
        return page.get("extract", "")
    return ""


def wp_url(title):
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(
        title.replace(" ", "_"), safe=""
    )


# ---------- Wikidata ----------

def wd_entity(qid):
    d = get_json(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json")
    return d["entities"][qid] if d else None


def wd_year(claims, prop):
    try:
        t = claims[prop][0]["mainsnak"]["datavalue"]["value"]["time"]
        return int(t[1:5]) * (-1 if t[0] == "-" else 1)
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def sparql_paintings(qid):
    # Inner query first narrows to the 60 most-sitelinked paintings, so the
    # expensive dimension paths and label service run on 60 rows, not thousands.
    q = f"""SELECT ?p ?pLabel ?image ?inception ?collectionLabel ?h ?w ?sitelinks ?article WHERE {{
  {{ SELECT ?p ?image ?sitelinks WHERE {{
       ?p wdt:P31 wd:Q3305213; wdt:P170 wd:{qid}; wdt:P18 ?image; wikibase:sitelinks ?sitelinks .
     }} ORDER BY DESC(?sitelinks) LIMIT 60 }}
  OPTIONAL {{ ?p wdt:P571 ?inception }}
  OPTIONAL {{ ?p wdt:P195 ?collection }}
  OPTIONAL {{ ?p p:P2048/psn:P2048/wikibase:quantityAmount ?h }}
  OPTIONAL {{ ?p p:P2049/psn:P2049/wikibase:quantityAmount ?w }}
  OPTIONAL {{ ?article schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY DESC(?sitelinks)"""
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q, safe="")
    d = None
    for attempt in range(3):
        try:
            d = get_json(url, sleep=SPARQL_SLEEP)
            break
        except RuntimeError as e:
            print(f"    sparql retry {attempt + 1} ({e})", flush=True)
            time.sleep(8 * (attempt + 1))
    if d is None:
        raise RuntimeError(f"SPARQL failed for {qid} after retries")
    rows, seen = [], set()
    for b in d["results"]["bindings"]:
        pqid = b["p"]["value"].rsplit("/", 1)[-1]
        if pqid in seen:
            continue
        seen.add(pqid)
        label = b.get("pLabel", {}).get("value", "")
        if not label or label == pqid:
            continue
        img = b["image"]["value"]  # Special:FilePath URL
        fname = urllib.parse.unquote(img.rsplit("/", 1)[-1]).replace("_", " ")
        year = None
        if "inception" in b:
            m = re.match(r"[+-]?(\d{4})", b["inception"]["value"])
            if m:
                year = int(m.group(1)) * (-1 if b["inception"]["value"].startswith("-") else 1)
        cm = None
        try:
            # psn: normalized to SI metres
            cm = {"w": round(float(b["w"]["value"]) * 100), "h": round(float(b["h"]["value"]) * 100)}
            if not (10 <= cm["w"] <= 1200 and 10 <= cm["h"] <= 1200):
                cm = None
        except (KeyError, ValueError):
            pass
        rows.append({
            "qid": pqid,
            "title": label,
            "file": "File:" + fname,
            "year": year,
            "cm": cm,
            "collection": b.get("collectionLabel", {}).get("value") or None,
            "sitelinks": int(b["sitelinks"]["value"]),
            "article": (
                urllib.parse.unquote(b["article"]["value"].rsplit("/wiki/", 1)[-1]).replace("_", " ")
                if "article" in b else None
            ),
        })
    return rows


def sparql_other_works(qid):
    """Non-painting works credited to the artist (sculptures, murals, prints...).
    Used only when the painting harvest leaves an artist below the gallery
    threshold, which happens for modern artists whose paintings are still
    under copyright."""
    q = f"""SELECT ?p ?pLabel ?typeLabel ?image ?inception ?collectionLabel ?sitelinks ?article WHERE {{
  {{ SELECT ?p ?image ?sitelinks WHERE {{
       ?p wdt:P170 wd:{qid}; wdt:P18 ?image; wikibase:sitelinks ?sitelinks .
       MINUS {{ ?p wdt:P31 wd:Q3305213 }}
     }} ORDER BY DESC(?sitelinks) LIMIT 40 }}
  OPTIONAL {{ ?p wdt:P31 ?type }}
  OPTIONAL {{ ?p wdt:P571 ?inception }}
  OPTIONAL {{ ?p wdt:P195 ?collection }}
  OPTIONAL {{ ?article schema:about ?p ; schema:isPartOf <https://en.wikipedia.org/> }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY DESC(?sitelinks)"""
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(q, safe="")
    d = None
    for attempt in range(3):
        try:
            d = get_json(url, sleep=SPARQL_SLEEP)
            break
        except RuntimeError as e:
            print(f"    sparql retry {attempt + 1} ({e})", flush=True)
            time.sleep(8 * (attempt + 1))
    if d is None:
        return []
    rows, seen = [], set()
    for b in d["results"]["bindings"]:
        pqid = b["p"]["value"].rsplit("/", 1)[-1]
        if pqid in seen:
            continue
        seen.add(pqid)
        label = b.get("pLabel", {}).get("value", "")
        if not label or label == pqid:
            continue
        type_label = b.get("typeLabel", {}).get("value", "")
        if NON_WORK_TYPES.search(type_label):
            continue
        img = b["image"]["value"]
        fname = urllib.parse.unquote(img.rsplit("/", 1)[-1]).replace("_", " ")
        year = None
        if "inception" in b:
            m = re.match(r"[+-]?(\d{4})", b["inception"]["value"])
            if m:
                year = int(m.group(1)) * (-1 if b["inception"]["value"].startswith("-") else 1)
        rows.append({
            "qid": pqid,
            "title": label,
            "file": "File:" + fname,
            "year": year,
            "cm": None,
            "collection": b.get("collectionLabel", {}).get("value") or None,
            "sitelinks": int(b["sitelinks"]["value"]),
            "article": (
                urllib.parse.unquote(b["article"]["value"].rsplit("/wiki/", 1)[-1]).replace("_", " ")
                if "article" in b else None
            ),
        })
    return rows


# ---------- Commons ----------

def commons_imageinfo(files, width):
    """Batched imageinfo for a list of 'File:...' titles at a given thumb width."""
    out = {}
    for i in range(0, len(files), 20):
        batch = files[i : i + 20]
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&format=json"
            "&prop=imageinfo&iiprop=url%7Csize%7Cextmetadata"
            f"&iiurlwidth={width}&redirects=1&titles="
            + urllib.parse.quote("|".join(batch), safe="")
        )
        d = get_json(url)
        if not d:
            continue
        redirect = {r["to"]: r["from"] for r in d["query"].get("redirects", [])}
        normalized = {n["to"]: n["from"] for n in d["query"].get("normalized", [])}
        for page in d["query"]["pages"].values():
            title = page.get("title", "")
            orig = normalized.get(title, title)
            orig = redirect.get(orig, orig)
            orig = normalized.get(orig, orig)
            info = (page.get("imageinfo") or [None])[0]
            if info:
                out[orig] = info
                out[title] = info
    return out


def license_ok(info):
    lic = (info.get("extmetadata", {}).get("LicenseShortName", {}).get("value") or "").lower()
    if BLOCKED_LICENSE.search(lic):
        return False, lic
    return any(k in lic for k in FREE_LICENSES), lic


# ---------- facts ----------

def extract_facts(article_title):
    text = wp_full_extract(article_title)
    if not text:
        return []
    chunks = re.split(r"\n==+\s*(.+?)\s*==+\n", text)
    # chunks = [lead, h1, body1, h2, body2, ...]
    section_bodies = []
    for i in range(1, len(chunks) - 1, 2):
        heading = chunks[i].strip()
        body = chunks[i + 1].strip()
        if heading.lower() in SECTION_STOPLIST or len(body) < 80:
            continue
        section_bodies.append((heading, body))
    section_bodies.sort(
        key=lambda hb: PREFERRED_SECTIONS.index(hb[0].lower())
        if hb[0].lower() in PREFERRED_SECTIONS else 99
    )
    facts = []
    base = wp_url(article_title)
    for heading, body in section_bodies[:3]:
        snippet = first_sentences(body, n=2, max_chars=350)
        if len(snippet) < 60:
            continue
        facts.append({
            "text": snippet,
            "section": heading,
            "source": base + "#" + urllib.parse.quote(heading.replace(" ", "_"), safe=""),
        })
    return facts


# ---------- main ----------

def build_artist(seed_artist, report):
    slug = seed_artist["slug"]
    title = seed_artist["wikipedia"]
    print(f"— {slug}", flush=True)

    qid = wp_qid(title)
    summary = wp_summary(title)
    entity = wd_entity(qid) if qid else None
    if not (qid and summary and entity):
        report[slug] = {"error": "could not resolve artist", "kept": 0}
        return None

    claims = entity.get("claims", {})
    # Ancient-era nodes are often works, sites or cultures rather than people;
    # seed.json may pin their dates (negative = BCE) when Wikidata has no P569/P570.
    born = sa_born if (sa_born := seed_artist.get("born")) is not None else wd_year(claims, "P569")
    died = sa_died if (sa_died := seed_artist.get("died")) is not None else wd_year(claims, "P570")
    one_liner = entity.get("descriptions", {}).get("en", {}).get("value", "")
    name = summary.get("title", title)
    portrait = summary.get("thumbnail", {}).get("source")

    rows = sparql_paintings(qid)

    include = set(seed_artist.get("include", []))
    exclude = set(seed_artist.get("exclude", []))
    rows = [r for r in rows if r["qid"] not in exclude]
    rows.sort(key=lambda r: (r["qid"] not in include, -r["sitelinks"]))

    # dedupe near-identical titles (versions of the same work)
    seen_labels, candidates = set(), []
    for r in rows:
        nl = norm_label(r["title"])
        if nl in seen_labels:
            continue
        seen_labels.add(nl)
        candidates.append(r)
    candidates = candidates[:30]

    kept, rejected = [], []
    max_p = seed_artist.get("maxPaintings", DEFAULT_MAX)

    def keep_rows(rows, min_px=1000):
        info640 = commons_imageinfo([r["file"] for r in rows], 640)
        have = {k["file"] for k in kept}
        for r in rows:
            if len(kept) >= max_p:
                break
            if r["file"] in have:
                continue
            info = info640.get(r["file"])
            if not info:
                rejected.append((r["title"], "no imageinfo"))
                continue
            ok, lic = license_ok(info)
            if not ok:
                rejected.append((r["title"], f"license: {lic or 'unknown'}"))
                continue
            if max(info.get("width", 0), info.get("height", 0)) < min_px:
                rejected.append((r["title"], f"too small: {info.get('width')}x{info.get('height')}"))
                continue
            r["_info640"] = info
            have.add(r["file"])
            kept.append(r)

    keep_rows(candidates)

    # Modern artists: copyrighted paintings leave the harvest short, so top up
    # with the artist's non-painting works (sculptures, murals, installations).
    if len(kept) < 6:
        others = [r for r in sparql_other_works(qid) if r["qid"] not in exclude]
        keep_rows(others)

    # Hand-curated Commons files from seed.json (verified by a human; smaller
    # minimum size since some legitimate early works only exist as small scans).
    curated = []
    for cw in seed_artist.get("commonsWorks", []):
        curated.append({
            "qid": None,
            "title": cw["title"],
            "file": cw["file"],
            "year": cw.get("year"),
            "cm": None,
            "collection": cw.get("collection"),
            "sitelinks": 0,
            "article": cw.get("article"),
        })
    keep_rows(curated, min_px=440)

    # Ancient-wing entities (seeded dates mark works, sites, cultures and
    # sculptors known only through copies): no Wikidata creator credits exist,
    # so hang the gallery with the images that illustrate the entity's own
    # Wikipedia article, under the same license and size gates.
    if len(kept) < max_p and ("born" in seed_artist or "activeStart" in seed_artist):
        article_rows = []
        for f in wp_article_images(title):
            fname = f[len("File:"):]
            clean = re.sub(r"\.[a-z0-9]+$", "", fname, flags=re.I).replace("_", " ")
            clean = re.sub(r"\s*\(.*?\)\s*$", "", clean).strip() or fname
            article_rows.append({
                "qid": None,
                "title": clean,
                "file": f,
                "year": None,
                "cm": None,
                "collection": None,
                "sitelinks": 0,
                "article": None,
            })
        keep_rows(article_rows, min_px=440)

    info1600 = commons_imageinfo([r["file"] for r in kept], 1600)

    # Ancient-wing works (article-image and curated harvests) have no article
    # of their own, so their placards are assembled from what Wikipedia and
    # Commons say about the exact image: the caption editors wrote for it on
    # the entity's article, else the Commons file description, always followed
    # by the entity's own lead sentences for plain-language context.
    ancient = "born" in seed_artist or "activeStart" in seed_artist
    captions = wp_article_captions(title) if ancient else {}
    entity_facts = extract_facts(title) if ancient else []
    entity_context = first_sentences(summary.get("extract", ""), n=2, max_chars=350)

    paintings = []
    for r in kept:
        i640, i1600 = r["_info640"], info1600.get(r["file"], r["_info640"])
        story = None
        facts = []
        if r["article"]:
            s = wp_summary(r["article"])
            if s and s.get("extract"):
                story = {
                    "extract": first_sentences(s["extract"], n=3, max_chars=600),
                    "source": wp_url(r["article"]),
                }
            facts = extract_facts(r["article"])
        if ancient and not story:
            caption = captions.get(r["file"])
            lead = caption or usable_desc(
                i640.get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
            )
            if lead and not re.search(r"[.!?]$", lead):
                lead += "."
            if lead:
                context = "" if len(lead) > 350 else entity_context
                extract = (lead + " " + context).strip()
            else:
                extract = first_sentences(summary.get("extract", ""), n=3, max_chars=600)
            if extract:
                story = {"extract": extract, "source": wp_url(title)}
                facts = entity_facts
            if caption and (junk_title(r["title"]) or len(r["title"]) > 90):
                r["title"] = title_from_caption(caption)
        credit = strip_html(i640.get("extmetadata", {}).get("Artist", {}).get("value", ""))
        lic_name = i640.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        paintings.append({
            "qid": r["qid"],
            "title": r["title"],
            "year": r["year"],
            "image": {
                "file": r["file"],
                "thumb640": i640.get("thumburl"),
                "thumb1600": i1600.get("thumburl"),
                "pxW": i640.get("width"),
                "pxH": i640.get("height"),
            },
            "cm": r["cm"],
            "collection": r["collection"],
            "story": story,
            "facts": facts,
            "license": {"name": lic_name, "credit": credit[:200]},
        })

    paintings.sort(key=lambda p: (p["year"] is None, p["year"] or 0))
    # Per-entity gate override for objects Commons genuinely has few photos of
    # (e.g. the Togatus Barberini exists in exactly two usable images).
    has_gallery = len(paintings) >= seed_artist.get("minPaintings", MIN_PAINTINGS)

    artist = {
        "slug": slug,
        "name": name,
        "qid": qid,
        "born": born,
        "died": died,
        "periods": seed_artist["periods"],
        "oneLiner": one_liner,
        "portrait": {"thumb": portrait},
        "bio": {
            "extract": first_sentences(summary.get("extract", ""), n=4, max_chars=700),
            "source": wp_url(title),
        },
        "wikipedia": wp_url(title),
        "hasGallery": has_gallery,
        "paintings": paintings,
    }
    report[slug] = {
        "kept": len(paintings),
        "hasGallery": has_gallery,
        "rejected": rejected[:12],
        "sparqlRows": len(rows),
    }
    return artist


def pack_lanes(periods):
    lanes_end = []
    for p in sorted(periods, key=lambda p: (p["start"], p["end"])):
        for i, end in enumerate(lanes_end):
            if p["start"] >= end - 2:  # small tolerated visual overlap
                p["lane"] = i
                lanes_end[i] = p["end"]
                break
        else:
            p["lane"] = len(lanes_end)
            lanes_end.append(p["end"])
    return periods


def main():
    only = None
    if "--artist" in sys.argv:
        only = set(sys.argv[sys.argv.index("--artist") + 1].split(","))
    CACHE.mkdir(exist_ok=True)
    (DATA / "artists").mkdir(parents=True, exist_ok=True)
    seed = json.loads((HERE / "seed.json").read_text(encoding="utf-8"))

    periods = []
    for p in seed["periods"]:
        s = wp_summary(p["wikipedia"])
        periods.append({
            "id": p["id"],
            "name": p["name"],
            "start": p["start"],
            "end": p["end"],
            "summary": first_sentences((s or {}).get("extract", ""), n=2, max_chars=320),
            "source": wp_url(p["wikipedia"]),
        })
    pack_lanes(periods)
    periods.sort(key=lambda p: p["start"])

    report = {}
    index_artists = []
    for sa in seed["artists"]:
        if only and sa["slug"] not in only:
            continue
        artist = build_artist(sa, report)
        if not artist:
            continue
        (DATA / "artists" / f"{artist['slug']}.json").write_text(
            json.dumps(artist, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        died = artist["died"]
        active_end = sa.get("activeEnd")
        if active_end is None:
            if died:
                active_end = died
            elif "born" in sa and artist["born"] is not None:
                # single-dated work/site: keep it anchored at its own year
                # rather than stretching to the period's end
                active_end = artist["born"]
            else:
                active_end = max(
                    (p["end"] for p in periods if p["id"] in artist["periods"]), default=CURRENT_YEAR
                )
        active_start = sa.get("activeStart")
        if active_start is None and artist["born"] is not None:
            # a seeded born year marks a work/site/culture: its dates ARE its
            # active span; a person starts working ~20 years after birth
            active_start = artist["born"] if "born" in sa else artist["born"] + 20
        index_artists.append({
            "slug": artist["slug"],
            "name": artist["name"],
            "born": artist["born"],
            "died": died,
            "activeStart": active_start,
            "activeEnd": active_end,
            "periods": artist["periods"],
            "oneLiner": artist["oneLiner"],
            "hasGallery": artist["hasGallery"],
            "paintingCount": len(artist["paintings"]),
            "portrait": artist["portrait"]["thumb"],
        })

    if not only:
        index = {
            "generated": time.strftime("%Y-%m-%d"),
            "license": "Text: Wikipedia, CC BY-SA 4.0. Images: Wikimedia Commons (public domain or Creative Commons; attribution on each work).",
            "periods": periods,
            "artists": index_artists,
        }
        (DATA / "index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    print("\n===== REPORT =====")
    galleries = 0
    for slug, r in report.items():
        if "error" in r:
            print(f"{slug:35s} ERROR: {r['error']}")
            continue
        mark = "GALLERY " if r["hasGallery"] else "placard-only"
        if r["hasGallery"]:
            galleries += 1
        print(f"{slug:35s} {r['kept']:2d} kept  ({r['sparqlRows']:3d} sparql rows)  {mark}")
        for t, why in r["rejected"]:
            print(f"    - rejected: {t[:50]:50s} {why}")
    print(f"\n{galleries} gallery artists / {len(report)} total")


if __name__ == "__main__":
    main()
